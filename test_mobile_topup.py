#!/usr/bin/env python3
"""
Test script for mobile top-up service
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'luna_iot_py.settings')
django.setup()

from api_common.services.mobile_topup_service import mobile_topup_service

def test_mobile_topup():
    """Test the mobile top-up service"""
    print("Testing Mobile Top-up Service")
    print("=" * 50)
    
    # Test data
    test_cases = [
        {
            'phone': '9822426473',  # Ncell number
            'amount': 100,
            'sim_type': 'NCELL'
        },
        {
            'phone': '9841234567',  # NTC number
            'amount': 50,
            'sim_type': 'NTC'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Phone: {test_case['phone']}")
        print(f"Amount: {test_case['amount']}")
        print(f"SIM Type: {test_case['sim_type']}")
        print("-" * 30)
        
        try:
            result = mobile_topup_service.process_topup(
                test_case['phone'],
                test_case['amount'],
                test_case['sim_type']
            )
            
            print(f"Success: {result['success']}")
            print(f"Message: {result['message']}")
            print(f"Reference: {result['reference']}")
            print(f"Status Code: {result['statusCode']}")
            print(f"State: {result['state']}")
            
            if result['data']:
                print(f"Data: {result['data']}")
                
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("-" * 30)

if __name__ == '__main__':
    test_mobile_topup()
