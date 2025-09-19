"""
Mobile Top-up Service
Handles mobile top-up requests directly in Python
Replicates the Node.js mobileTopupService.js functionality
"""
import requests
import json
import time
import random
import string
from django.conf import settings


class MobileTopupService:
    """
    Service to handle mobile top-up requests
    Replicates Node.js mobileTopupService.js functionality
    """
    
    def __init__(self):
        # Mobile top-up API configuration
        self.base_url = 'https://smartdigitalnepal.com/'
        self.token = 'EMQx29Ap6KmSs2DWD0RiYs8EnrPZfv+Ga0Q2wLG4Ql0='
        
        # API Endpoints
        self.endpoints = {
            'ntc': 'https://smartdigitalnepal.com/api/service/topup-ntc',
            'ncell': 'https://smartdigitalnepal.com/api/service/topup-ncell'
        }
        
        # Amount limits
        self.limits = {
            'ntc': {'min': 20, 'max': 25000},
            'ncell': {'min': 50, 'max': 5000}
        }
        
        # SIM type mapping
        self.sim_types = {
            'NTC': 'ntc',
            'NCELL': 'ncell'
        }
    
    def generate_reference_id(self):
        """
        Generate unique reference ID
        """
        timestamp = int(time.time() * 1000)
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f'RCH_{timestamp}_{random_str}'
    
    def validate_phone_number(self, phone):
        """
        Validate phone number format
        """
        # Remove any non-digit characters
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # Check if it's a 10-digit number
        if len(clean_phone) != 10:
            raise ValueError('Phone number must be 10 digits')
        
        return clean_phone
    
    def determine_sim_type(self, phone):
        """
        Determine SIM type based on phone number
        """
        clean_phone = self.validate_phone_number(phone)
        prefix = clean_phone[:3]
        
        # NTC prefixes
        if prefix in ['984', '985', '986']:
            return 'ntc'
        # Ncell prefixes
        elif prefix in ['980', '981', '982', '987', '988', '989']:
            return 'ncell'
        
        raise ValueError('Unable to determine SIM type from phone number')
    
    def validate_amount(self, amount, sim_type):
        """
        Validate amount based on SIM type
        """
        if sim_type not in self.limits:
            raise ValueError(f'Invalid SIM type: {sim_type}')
        
        limits = self.limits[sim_type]
        if amount < limits['min'] or amount > limits['max']:
            raise ValueError(f'Amount must be between {limits["min"]} and {limits["max"]} for {sim_type.upper()}')
        
        return True
    
    def topup_ntc(self, phone, amount, reference):
        """
        Make top-up request to NTC
        """
        try:
            request_data = {
                'token': self.token,
                'reference': reference,
                'amount': str(amount),
                'number': phone
            }
            
            
            response = requests.post(
                self.endpoints['ntc'],
                json=request_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            
            # Check if response is empty
            if not response.text.strip():
                return {
                    'success': False,
                    'message': 'NTC API returned empty response',
                    'data': None,
                    'statusCode': response.status_code,
                    'state': 'Failed',
                    'description': 'Empty response from NTC API'
                }
            
            # Check if response is HTML (error page)
            if response.text.strip().startswith('<!DOCTYPE html>') or response.text.strip().startswith('<html'):
                return {
                    'success': False,
                    'message': 'NTC API returned HTML error page instead of JSON',
                    'data': None,
                    'statusCode': response.status_code,
                    'state': 'Failed',
                    'description': f'API endpoint may be incorrect or service down. Response: {response.text[:200]}...'
                }
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except ValueError as json_error:
                return {
                    'success': False,
                    'message': f'NTC API returned invalid JSON: {response.text[:100]}',
                    'data': None,
                    'statusCode': response.status_code,
                    'state': 'Failed',
                    'description': f'JSON parse error: {str(json_error)}'
                }
            
            return {
                'success': response_data.get('Status', False),
                'message': response_data.get('Message', ''),
                'data': response_data.get('Data'),
                'statusCode': response_data.get('StatusCode', response.status_code),
                'state': response_data.get('State', ''),
                'description': response_data.get('Description', '')
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'NTC Top-up failed: {str(e)}',
                'data': None,
                'statusCode': 500,
                'state': 'Failed',
                'description': str(e)
            }
    
    def topup_ncell(self, phone, amount, reference):
        """
        Make top-up request to Ncell
        """
        try:
            request_data = {
                'token': self.token,
                'reference': reference,
                'amount': str(amount),
                'number': phone
            }
            
            
            response = requests.post(
                self.endpoints['ncell'],
                json=request_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            
            # Check if response is empty
            if not response.text.strip():
                return {
                    'success': False,
                    'message': 'Ncell API returned empty response',
                    'data': None,
                    'statusCode': response.status_code,
                    'state': 'Failed',
                    'description': 'Empty response from Ncell API'
                }
            
            # Check if response is HTML (error page)
            if response.text.strip().startswith('<!DOCTYPE html>') or response.text.strip().startswith('<html'):
                return {
                    'success': False,
                    'message': 'Ncell API returned HTML error page instead of JSON',
                    'data': None,
                    'statusCode': response.status_code,
                    'state': 'Failed',
                    'description': f'API endpoint may be incorrect or service down. Response: {response.text[:200]}...'
                }
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except ValueError as json_error:
                return {
                    'success': False,
                    'message': f'Ncell API returned invalid JSON: {response.text[:100]}',
                    'data': None,
                    'statusCode': response.status_code,
                    'state': 'Failed',
                    'description': f'JSON parse error: {str(json_error)}'
                }
            
            return {
                'success': response_data.get('Status', False),
                'message': response_data.get('Message', ''),
                'data': response_data.get('Data'),
                'statusCode': response_data.get('StatusCode', response.status_code),
                'state': response_data.get('State', ''),
                'description': response_data.get('Description', '')
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'Ncell Top-up failed: {str(e)}',
                'data': None,
                'statusCode': 500,
                'state': 'Failed',
                'description': str(e)
            }
    
    def process_topup(self, phone, amount, device_sim_type=None):
        """
        Process mobile top-up based on SIM type
        """
        try:
            # Validate phone number
            clean_phone = self.validate_phone_number(phone)
            
            # Determine SIM type (use device SIM type or auto-detect)
            if device_sim_type and device_sim_type.upper() in self.sim_types:
                sim_type = self.sim_types[device_sim_type.upper()]
            else:
                sim_type = self.determine_sim_type(clean_phone)
            
            # Validate amount for the SIM type
            self.validate_amount(amount, sim_type)
            
            # Generate unique reference
            reference = self.generate_reference_id()
            
            
            # Make the appropriate API call
            if sim_type == 'ntc':
                result = self.topup_ntc(clean_phone, amount, reference)
            elif sim_type == 'ncell':
                result = self.topup_ncell(clean_phone, amount, reference)
            else:
                raise ValueError(f'Unsupported SIM type: {sim_type}')
            
            # Add additional metadata
            result['simType'] = sim_type.upper()
            result['phone'] = clean_phone
            result['amount'] = amount
            result['reference'] = reference
            result['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            return result
            
        except Exception as e:
            
            return {
                'success': False,
                'message': str(e),
                'data': None,
                'statusCode': 400,
                'state': 'Failed',
                'description': str(e),
                'simType': device_sim_type or 'UNKNOWN',
                'phone': phone,
                'amount': amount,
                'reference': f'ERROR_{phone}_{amount}',
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            }


# Create singleton instance
mobile_topup_service = MobileTopupService()
