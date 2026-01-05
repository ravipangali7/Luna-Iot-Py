"""
Phone Book Number Importer Service
Handles parsing and importing CSV/XLSX files containing phone book contacts
"""
import pandas as pd
from django.db import transaction
from phone_call.models import PhoneBookNumber, PhoneBook


class PhoneBookNumberImporter:
    """Service to import phone book number data from CSV/XLSX files"""
    
    REQUIRED_COLUMNS = ['Name', 'Phone']
    
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
        """Parse XLSX/XLS file using pandas"""
        try:
            # Read Excel file
            df = pd.read_excel(file, engine='openpyxl')
            return df
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {str(e)}")
    
    def validate_file_structure(self, df):
        """Validate that the file has required columns"""
        # Normalize column names (strip whitespace, case-insensitive)
        df.columns = df.columns.str.strip()
        normalized_columns = {col.lower(): col for col in df.columns}
        
        missing_columns = []
        for required_col in self.REQUIRED_COLUMNS:
            if required_col.lower() not in normalized_columns:
                missing_columns.append(required_col)
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        return True
    
    def import_phone_book_numbers(self, file, phone_book_id, file_type='csv'):
        """
        Main import logic
        
        Args:
            file: File object (CSV or XLSX)
            phone_book_id: ID of the phone book to import numbers into
            file_type: 'csv' or 'xlsx'
        
        Returns:
            dict with import statistics
        """
        self.errors = []
        self.success_count = 0
        self.failed_count = 0
        
        try:
            # Get phone book
            try:
                phone_book = PhoneBook.objects.get(id=phone_book_id)
            except PhoneBook.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Phone book not found',
                    'total_rows': 0,
                    'successful': 0,
                    'failed': 0,
                    'errors': []
                }
            
            # Parse file based on type
            if file_type.lower() == 'csv':
                df = self.parse_csv_file(file)
            elif file_type.lower() in ['xlsx', 'xls']:
                df = self.parse_excel_file(file)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Validate file structure
            self.validate_file_structure(df)
            
            # Normalize column names for case-insensitive matching
            df.columns = df.columns.str.strip()
            column_map = {col.lower(): col for col in df.columns}
            
            self.total_rows = len(df)
            
            # Process each row
            created_numbers = []
            for index, row in df.iterrows():
                try:
                    with transaction.atomic():
                        # Get values (case-insensitive)
                        name = str(row[column_map['name']]).strip() if pd.notna(row[column_map['name']]) else ''
                        phone = str(row[column_map['phone']]).strip() if pd.notna(row[column_map['phone']]) else ''
                        
                        # Validate required fields
                        if not name:
                            raise ValueError("Name is required")
                        if not phone:
                            raise ValueError("Phone is required")
                        
                        # Check for duplicate phone number in this phone book
                        existing = PhoneBookNumber.objects.filter(
                            phonebook=phone_book,
                            phone=phone
                        ).first()
                        
                        if existing:
                            # Update existing record
                            existing.name = name
                            existing.save()
                            created_numbers.append({
                                'name': name,
                                'phone': phone,
                                'action': 'updated'
                            })
                        else:
                            # Create new record
                            number = PhoneBookNumber.objects.create(
                                phonebook=phone_book,
                                name=name,
                                phone=phone
                            )
                            created_numbers.append({
                                'name': name,
                                'phone': phone,
                                'action': 'created'
                            })
                        
                        self.success_count += 1
                        
                except Exception as e:
                    self.failed_count += 1
                    error_msg = f"Row {index + 2}: {str(e)}"  # +2 because index is 0-based and we have header
                    self.errors.append(error_msg)
            
            return {
                'success': True,
                'total_rows': self.total_rows,
                'successful': self.success_count,
                'failed': self.failed_count,
                'errors': self.errors[:100],  # Limit to first 100 errors
                'created_numbers': created_numbers[:100]  # Limit to first 100 for response size
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
