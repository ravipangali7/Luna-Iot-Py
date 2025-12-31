"""
SIM Balance Importer Service
Handles parsing and importing CSV/XLSX files containing SIM balance and free resource data
"""
import pandas as pd
import re
from datetime import datetime
from django.db import transaction
from device.models import Device
from shared.models import SimBalance, SimFreeResource, ResourceType


class SimBalanceImporter:
    """Service to import SIM balance data from CSV/XLSX files"""
    
    REQUIRED_COLUMNS = ['Number', 'State', 'Balance', 'Balance Expiry', 'Free Resource']
    
    def __init__(self):
        self.errors = []
        self.success_count = 0
        self.failed_count = 0
        self.total_rows = 0
    
    def parse_csv_file(self, file):
        """Parse CSV file using pandas"""
        try:
            # Read CSV file
            df = pd.read_csv(file, encoding='utf-8')
            return df
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {str(e)}")
    
    def parse_excel_file(self, file):
        """Parse XLSX file using pandas"""
        try:
            # Read Excel file
            df = pd.read_excel(file, engine='openpyxl')
            return df
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {str(e)}")
    
    def validate_file_structure(self, df):
        """Validate that the file has required columns"""
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        return True
    
    def extract_mb_from_name(self, name):
        """
        Extract MB value from name field (e.g., 'm2m 50mb' -> 50)
        """
        if not name:
            return None
        
        # Pattern to match number before 'mb' or 'MB' (case-insensitive)
        pattern = r'(\d+(?:\.\d+)?)\s*mb'
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None
    
    def extract_mb_from_remaining(self, remaining):
        """
        Extract MB value from remaining field (e.g., '49.83MB' -> 49.83)
        """
        if not remaining:
            return None
        
        # Pattern to match decimal number before 'MB' (case-insensitive)
        pattern = r'(\d+(?:\.\d+)?)\s*mb'
        match = re.search(pattern, remaining, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None
    
    def parse_free_resources(self, free_resource_text):
        """
        Parse multi-line free resource text
        
        Format: "name: X, type: Y, remaining: Z, expiry: W"
        Multiple resources separated by newlines
        
        Only processes DATA type resources and extracts MB values
        """
        resources = []
        if not free_resource_text or pd.isna(free_resource_text):
            return resources
        
        # Convert to string and split by newlines
        text = str(free_resource_text).strip()
        if not text:
            return resources
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse line: "name: m2m 50mb, type: DATA, remaining: 49.83MB, expiry: 2026-03-29 11:34:00"
            resource = {}
            parts = line.split(',')
            
            for part in parts:
                part = part.strip()
                if 'name:' in part:
                    resource['name'] = part.split('name:')[1].strip()
                elif 'type:' in part:
                    resource['type'] = part.split('type:')[1].strip()
                elif 'remaining:' in part:
                    resource['remaining'] = part.split('remaining:')[1].strip()
                elif 'expiry:' in part:
                    expiry_str = part.split('expiry:')[1].strip()
                    try:
                        resource['expiry'] = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        # Try alternative format
                        try:
                            resource['expiry'] = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S.%f')
                        except ValueError:
                            self.errors.append(f"Invalid expiry format: {expiry_str}")
                            continue
            
            # Validate resource has all required fields
            if all(key in resource for key in ['name', 'type', 'remaining', 'expiry']):
                # Only process DATA type resources
                resource_type = resource['type'].upper()
                if resource_type == ResourceType.DATA or 'DATA' in resource_type:
                    # Extract MB values
                    resource['data_plan_mb'] = self.extract_mb_from_name(resource['name'])
                    resource['remaining_mb'] = self.extract_mb_from_remaining(resource['remaining'])
                    resources.append(resource)
                # Ignore SMS and VOICE resources
        
        return resources
    
    def parse_balance_expiry(self, expiry_str):
        """Parse balance expiry date string"""
        if pd.isna(expiry_str) or not expiry_str:
            return None
        
        try:
            # Try standard format: "2026-10-20 23:59:59"
            return datetime.strptime(str(expiry_str).strip(), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                # Try alternative format with microseconds
                return datetime.strptime(str(expiry_str).strip(), '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                # Try date only
                try:
                    return datetime.strptime(str(expiry_str).strip(), '%Y-%m-%d')
                except ValueError:
                    return None
    
    def import_sim_data(self, file, file_type='csv'):
        """
        Main import logic
        
        Args:
            file: File object (CSV or XLSX)
            file_type: 'csv' or 'xlsx'
        
        Returns:
            dict with import statistics
        """
        self.errors = []
        self.success_count = 0
        self.failed_count = 0
        
        try:
            # Parse file based on type
            if file_type.lower() == 'csv':
                df = self.parse_csv_file(file)
            elif file_type.lower() in ['xlsx', 'xls']:
                df = self.parse_excel_file(file)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Validate file structure
            self.validate_file_structure(df)
            
            self.total_rows = len(df)
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    with transaction.atomic():
                        self._process_row(row, index + 1)
                except Exception as e:
                    self.failed_count += 1
                    error_msg = f"Row {index + 1}: {str(e)}"
                    self.errors.append(error_msg)
            
            return {
                'success': True,
                'total_rows': self.total_rows,
                'successful': self.success_count,
                'failed': self.failed_count,
                'errors': self.errors[:100]  # Limit to first 100 errors
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'total_rows': self.total_rows,
                'successful': self.success_count,
                'failed': self.failed_count,
                'errors': self.errors
            }
    
    def _process_row(self, row, row_number):
        """Process a single row from the file"""
        try:
            # Extract data from row
            phone_number = str(row['Number']).strip()
            state = str(row['State']).strip() if pd.notna(row['State']) else 'ACTIVE'
            balance = float(row['Balance']) if pd.notna(row['Balance']) else 0.00
            balance_expiry = self.parse_balance_expiry(row['Balance Expiry'])
            free_resource_text = row['Free Resource'] if 'Free Resource' in row else None
            
            # Validate phone number
            if not phone_number:
                raise ValueError("Phone number is required")
            
            # Find device by phone number
            device = None
            try:
                device = Device.objects.get(phone=phone_number)
            except Device.DoesNotExist:
                # Device not found - still create SimBalance but without device link
                pass
            except Device.MultipleObjectsReturned:
                # Multiple devices with same phone - use first one
                device = Device.objects.filter(phone=phone_number).first()
            
            # Create or update SimBalance
            sim_balance, created = SimBalance.objects.update_or_create(
                phone_number=phone_number,
                defaults={
                    'device': device,
                    'state': state,
                    'balance': balance,
                    'balance_expiry': balance_expiry
                }
            )
            
            # Parse and update free resources
            if free_resource_text:
                resources = self.parse_free_resources(free_resource_text)
                
                # Delete old resources for this SIM
                SimFreeResource.objects.filter(sim_balance=sim_balance).delete()
                
                # Create new resources (only DATA type resources are returned from parse_free_resources)
                for resource in resources:
                    SimFreeResource.objects.create(
                        sim_balance=sim_balance,
                        name=resource['name'],
                        resource_type=ResourceType.DATA,
                        remaining=resource['remaining'],
                        expiry=resource['expiry'],
                        data_plan_mb=resource.get('data_plan_mb'),
                        remaining_mb=resource.get('remaining_mb')
                    )
            
            self.success_count += 1
        
        except Exception as e:
            raise Exception(f"Error processing row: {str(e)}")

