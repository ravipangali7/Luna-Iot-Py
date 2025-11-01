import requests
from django.conf import settings
from typing import Dict, Any, Optional
from urllib.parse import urlencode

class SMSService:
    """
    SMS Service for sending SMS messages via external API
    Matches Node.js SMSService functionality
    """
    
    def __init__(self):
        self.config = {
            'API_KEY': getattr(settings, 'SMS_API_KEY', '568383D0C5AA82'),
            'API_URL': getattr(settings, 'SMS_API_URL', 'https://sms.kaichogroup.com/smsapi/index.php'),
            'CAMPAIGN_ID': getattr(settings, 'SMS_CAMPAIGN_ID', '9148'),
            'ROUTE_ID': getattr(settings, 'SMS_ROUTE_ID', '130'),
            'SENDER_ID': getattr(settings, 'SMS_SENDER_ID', 'SMSBit')
        }
    
    def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send SMS to phone number
        
        Args:
            phone_number (str): Phone number to send SMS to
            message (str): Message content to send
            
        Returns:
            Dict[str, Any]: Result containing success status and message
        """
        print(f"[DEBUG SMS] send_sms() - Phone: {phone_number}, Message: {message}")
        try:
            # Prepare parameters
            params = {
                'key': self.config['API_KEY'],
                'campaign': self.config['CAMPAIGN_ID'],
                'routeid': self.config['ROUTE_ID'],
                'type': 'text',
                'contacts': phone_number,
                'senderid': self.config['SENDER_ID'],
                'msg': message
            }
            
            # Build URL with proper encoding
            url = f"{self.config['API_URL']}?{urlencode(params)}"
            print(f"[DEBUG SMS] send_sms() - API URL: {self.config['API_URL']}")
            print(f"[DEBUG SMS] send_sms() - Parameters: {dict((k, v if k != 'key' else '***') for k, v in params.items())}")
            
            # Send request
            print(f"[DEBUG SMS] send_sms() - Sending request to SMS API...")
            response = requests.get(url, timeout=30)
            
            # Check if SMS was sent successfully
            print(f"[DEBUG SMS] send_sms() - Response status code: {response.status_code}")
            if response.status_code == 200:
                response_data = response.text.strip()
                print(f"[DEBUG SMS] send_sms() - Response data: {response_data}")
                
                # The API returns "SMS-SHOOT-ID/..." when successful
                if 'SMS-SHOOT-ID' in response_data:
                    print(f"[DEBUG SMS] send_sms() - SMS sent successfully to {phone_number}")
                    return {
                        'success': True, 
                        'message': 'SMS sent successfully',
                        'response': response_data
                    }
                elif 'ERR:' in response_data:
                    print(f"[DEBUG SMS] send_sms() - SMS service error for {phone_number}: {response_data}")
                    return {
                        'success': False, 
                        'message': f'SMS service error: {response_data}',
                        'response': response_data
                    }
                else:
                    print(f"[DEBUG SMS] send_sms() - Unexpected response for {phone_number}: {response_data}")
                    return {
                        'success': False, 
                        'message': f'Unexpected response from SMS service: {response_data}',
                        'response': response_data
                    }
            else:
                print(f"[DEBUG SMS] send_sms() - Failed with status code {response.status_code} for {phone_number}")
                return {
                    'success': False, 
                    'message': f'SMS API returned status code: {response.status_code}',
                    'response': response.text
                }
                
        except requests.exceptions.Timeout:
            print(f"[DEBUG SMS] send_sms() - Timeout error for {phone_number}")
            return {
                'success': False, 
                'message': 'SMS service timeout - request took too long'
            }
        except requests.exceptions.ConnectionError:
            print(f"[DEBUG SMS] send_sms() - Connection error for {phone_number}")
            return {
                'success': False, 
                'message': 'SMS service connection error - unable to reach API'
            }
        except Exception as e:
            print(f"[DEBUG SMS] send_sms() - Exception for {phone_number}: {str(e)}")
            return {
                'success': False, 
                'message': f'SMS service error: {str(e)}'
            }
    
    def send_otp(self, phone_number: str, otp: str) -> Dict[str, Any]:
        """
        Send OTP SMS to phone number
        
        Args:
            phone_number (str): Phone number to send OTP to
            otp (str): OTP code to send
            
        Returns:
            Dict[str, Any]: Result containing success status and message
        """
        message = f"Your Luna IoT verification code is: {otp}. Valid for 10 minutes."
        return self.send_sms(phone_number, message)
    
    def send_server_point_command(self, phone_number: str, server_ip: str = "38.54.71.218", port: str = "6666") -> Dict[str, Any]:
        """
        Send server point command via SMS
        
        Args:
            phone_number (str): Phone number to send command to
            server_ip (str): Server IP address
            port (str): Server port
            
        Returns:
            Dict[str, Any]: Result containing success status and message
        """
        message = f"SERVER,0,{server_ip},{port},0#"
        return self.send_sms(phone_number, message)
    
    def send_reset_command(self, phone_number: str) -> Dict[str, Any]:
        """
        Send reset command via SMS
        
        Args:
            phone_number (str): Phone number to send command to
            
        Returns:
            Dict[str, Any]: Result containing success status and message
        """
        message = "RESET#"
        return self.send_sms(phone_number, message)
    
    def send_relay_command(self, phone_number: str, relay_state: bool) -> Dict[str, Any]:
        """
        Send relay command via SMS
        
        Args:
            phone_number (str): Phone number to send command to
            relay_state (bool): True for ON, False for OFF
            
        Returns:
            Dict[str, Any]: Result containing success status and message
        """
        message = f"RELAY,{1 if relay_state else 0}#"
        return self.send_sms(phone_number, message)
    
    def send_relay_on_command(self, phone_number: str) -> Dict[str, Any]:
        """
        Send relay ON command via SMS
        
        Args:
            phone_number (str): Phone number to send command to
            
        Returns:
            Dict[str, Any]: Result containing success status and message
        """
        print(f"[DEBUG SMS] send_relay_on_command() - Sending RELAY ON to {phone_number}")
        message = "RELAY,1#"
        print(f"[DEBUG SMS] send_relay_on_command() - Command message: {message}")
        result = self.send_sms(phone_number, message)
        print(f"[DEBUG SMS] send_relay_on_command() - Result: success={result.get('success')}, message={result.get('message')}")
        return result
    
    def send_relay_off_command(self, phone_number: str) -> Dict[str, Any]:
        """
        Send relay OFF command via SMS
        
        Args:
            phone_number (str): Phone number to send command to
            
        Returns:
            Dict[str, Any]: Result containing success status and message
        """
        print(f"[DEBUG SMS] send_relay_off_command() - Sending RELAY OFF to {phone_number}")
        message = "RELAY,0#"
        print(f"[DEBUG SMS] send_relay_off_command() - Command message: {message}")
        result = self.send_sms(phone_number, message)
        print(f"[DEBUG SMS] send_relay_off_command() - Result: success={result.get('success')}, message={result.get('message')}")
        return result


# Create singleton instance
sms_service = SMSService()