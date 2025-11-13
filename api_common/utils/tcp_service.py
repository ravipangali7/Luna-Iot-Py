"""
TCP Service for sending relay commands via Node.js TCP service
Replaces SMS relay commands with TCP commands
"""
import requests
import logging
from django.conf import settings
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TCPService:
    """
    TCP Service for sending relay commands via Node.js TCP service
    Matches Node.js tcpService.sendRelayCommand functionality
    """
    
    def __init__(self):
        self.config = {
            'API_BASE_URL': getattr(settings, 'NODEJS_API_BASE_URL', 'https://www.system.mylunago.com'),
            'RELAY_COMMAND_ENDPOINT': '/api/relay-command'
        }
    
    def send_relay_command(self, imei: str, command: str) -> Dict[str, Any]:
        """
        Send relay command via TCP
        
        Args:
            imei (str): Device IMEI to send command to
            command (str): Command to send ('on', 'off', '1', or '0')
            
        Returns:
            Dict[str, Any]: Result containing success status and message
        """
        try:
            # Normalize command
            normalized_command = str(command).lower()
            
            if normalized_command not in ['on', 'off', '1', '0']:
                return {
                    'success': False,
                    'message': f'Invalid command: {command}. Use "on", "off", "1", or "0"'
                }
            
            # Prepare request payload
            payload = {
                'imei': imei,
                'command': normalized_command
            }
            
            # Build URL
            url = f"{self.config['API_BASE_URL']}{self.config['RELAY_COMMAND_ENDPOINT']}"
            
            # Send request
            response = requests.post(url, json=payload, timeout=30)
            
            # Check response
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get('success'):
                    return {
                        'success': True,
                        'message': response_data.get('message', 'Relay command sent successfully'),
                        'response': response_data
                    }
                else:
                    return {
                        'success': False,
                        'message': response_data.get('message', 'Failed to send relay command'),
                        'response': response_data
                    }
            else:
                return {
                    'success': False,
                    'message': f'TCP service returned status code: {response.status_code}',
                    'response': response.text
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': 'TCP service timeout - request took too long'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': 'TCP service connection error - unable to reach Node.js API'
            }
        except Exception as e:
            logger.error(f'Error sending relay command via TCP: {str(e)}')
            return {
                'success': False,
                'message': f'TCP service error: {str(e)}'
            }
    
    def send_relay_on_command(self, imei: str) -> Dict[str, Any]:
        """
        Send relay ON command via TCP
        
        Args:
            imei (str): Device IMEI to send command to
            
        Returns:
            Dict[str, Any]: Result containing success status and message
        """
        return self.send_relay_command(imei, 'on')
    
    def send_relay_off_command(self, imei: str) -> Dict[str, Any]:
        """
        Send relay OFF command via TCP
        
        Args:
            imei (str): Device IMEI to send command to
            
        Returns:
            Dict[str, Any]: Result containing success status and message
        """
        return self.send_relay_command(imei, 'off')


# Create singleton instance
tcp_service = TCPService()

