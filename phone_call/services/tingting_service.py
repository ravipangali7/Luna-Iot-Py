"""
TingTing API Service
Handles all API calls to TingTing telephony service
"""
import requests
import logging
from django.conf import settings
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class TingTingService:
    """
    Service class for interacting with TingTing API
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'TINGTING_API_KEY', '')
        self.base_url = getattr(settings, 'TINGTING_API_BASE_URL', 'https://app.tingting.io/api/v1')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     files: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to TingTing API
        
        Args:
            method: HTTP method (GET, POST, DELETE, PATCH)
            endpoint: API endpoint (relative to base_url)
            data: Request body data (for POST/PATCH)
            files: Files to upload (for multipart/form-data)
            params: Query parameters
            
        Returns:
            Dict with 'success', 'data', and 'error' keys
        """
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            # Prepare headers
            request_headers = self.headers.copy()
            if files:
                # Remove Content-Type for file uploads (let requests set it)
                request_headers.pop('Content-Type', None)
            
            # Log request details (mask sensitive data)
            log_headers = request_headers.copy()
            if 'Authorization' in log_headers:
                # Mask the token for security
                auth_header = log_headers['Authorization']
                if 'Bearer' in auth_header:
                    token = auth_header.split('Bearer ')[1]
                    masked_token = token[:10] + '...' + token[-5:] if len(token) > 15 else '***'
                    log_headers['Authorization'] = f'Bearer {masked_token}'
            
            print(f"[TingTing API] Request: {method.upper()} {url}")
            print(f"[TingTing API] Headers: {log_headers}")
            if params:
                print(f"[TingTing API] Query Params: {params}")
            if data and not files:
                print(f"[TingTing API] Request Body (JSON): {data}")
            elif data and files:
                print(f"[TingTing API] Request Data: {data}")
                print(f"[TingTing API] Files: {list(files.keys())}")
            
            # Make request
            if method.upper() == 'GET':
                response = requests.get(url, headers=request_headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                if files:
                    response = requests.post(url, headers=request_headers, data=data, files=files, timeout=60)
                else:
                    # Send JSON data (even if empty {}) with Content-Type header
                    response = requests.post(url, headers=request_headers, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=request_headers, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=request_headers, timeout=30)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, headers=request_headers, json=data, timeout=30)
            else:
                return {'success': False, 'error': f'Unsupported HTTP method: {method}'}
            
            # Log response details
            print(f"[TingTing API] Response Status: {response.status_code}")
            try:
                response_data = response.json()
                print(f"[TingTing API] Response Body: {response_data}")
            except ValueError:
                response_text = response.text[:500] if response.text else "No response body"
                print(f"[TingTing API] Response Body (non-JSON): {response_text}")
            
            # Handle response
            if response.status_code in [200, 201, 204]:
                if response.status_code == 204:
                    return {'success': True, 'data': {'message': 'Successfully deleted'}}
                
                try:
                    response_data = response.json()
                    return {'success': True, 'data': response_data}
                except ValueError:
                    # Response might be empty or not JSON
                    return {'success': True, 'data': {'message': 'Operation successful'}}
            else:
                error_msg = f'API returned status {response.status_code}'
                validation_errors = {}
                try:
                    error_data = response.json()
                    print(f"[TingTing API] ERROR Response: {error_data}")
                    
                    # Try to get standard error message
                    error_msg = error_data.get('message', error_data.get('error', error_msg))
                    
                    # Parse validation errors into user-friendly format
                    error_messages = []
                    if isinstance(error_data, dict):
                        for field, errors in error_data.items():
                            if field in ['message', 'error', 'detail']:
                                continue
                            if isinstance(errors, list):
                                error_messages.append(f"{field.replace('_', ' ').title()}: {', '.join(errors)}")
                                validation_errors[field] = errors
                            elif isinstance(errors, dict):
                                # Handle nested errors like {'voice': {'non_field_errors': [...]}}
                                for key, value in errors.items():
                                    if isinstance(value, list):
                                        error_messages.append(f"{field.replace('_', ' ').title()} ({key.replace('_', ' ').title()}): {', '.join(value)}")
                                        validation_errors[field] = {key: value}
                                    else:
                                        error_messages.append(f"{field.replace('_', ' ').title()} ({key.replace('_', ' ').title()}): {str(value)}")
                                        validation_errors[field] = {key: str(value)}
                            else:
                                error_messages.append(f"{field.replace('_', ' ').title()}: {str(errors)}")
                                validation_errors[field] = str(errors)
                    
                    # If we have validation errors, use them as the main error message
                    if error_messages:
                        error_msg = '; '.join(error_messages)
                    
                    # Log full error details
                    if 'detail' in error_data:
                        print(f"[TingTing API] ERROR Detail: {error_data['detail']}")
                    if 'errors' in error_data:
                        print(f"[TingTing API] ERROR Validation Errors: {error_data['errors']}")
                except ValueError:
                    error_text = response.text or error_msg
                    print(f"[TingTing API] ERROR Response (non-JSON): {error_text}")
                    error_msg = error_text
                
                return {
                    'success': False, 
                    'error': error_msg, 
                    'status_code': response.status_code,
                    'validation_errors': validation_errors if validation_errors else None
                }
                
        except requests.exceptions.Timeout:
            print(f"[TingTing API] ERROR: Timeout for {endpoint}")
            return {'success': False, 'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            print(f"[TingTing API] ERROR: Request error for {endpoint}: {str(e)}")
            return {'success': False, 'error': f'Request failed: {str(e)}'}
        except Exception as e:
            print(f"[TingTing API] ERROR: Unexpected error calling {endpoint}: {str(e)}")
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    # Voice Models
    def get_voice_models(self) -> Dict[str, Any]:
        """Get available voice models"""
        return self._make_request('GET', 'voice-models/')
    
    # Phone Numbers
    def get_active_phone_numbers(self) -> Dict[str, Any]:
        """Get active phone numbers"""
        return self._make_request('GET', 'phone-number/active/')
    
    # Campaigns
    def get_campaigns(self, page: Optional[int] = None) -> Dict[str, Any]:
        """Get all campaigns with optional pagination"""
        params = {'page': page} if page else None
        return self._make_request('GET', 'campaign/', params=params)
    
    def get_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Get campaign by ID"""
        return self._make_request('GET', f'campaign/{campaign_id}/')
    
    def create_campaign(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new campaign"""
        return self._make_request('POST', 'campaign/create/', data=data)
    
    def update_campaign(self, campaign_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing campaign"""
        # Use PUT method - TingTing API doesn't accept POST for updates
        return self._make_request('PUT', f'campaign/{campaign_id}/', data=data)
    
    def add_voice_assistance(self, campaign_id: int, voice_id: int, category: str = "Text") -> Dict[str, Any]:
        """Add voice assistance to a campaign"""
        data = {
            "voice": voice_id,  # Integer, not dict
            "category": category
        }
        # Try different endpoints and methods for voice assistance
        # First try: PUT to campaign/create/{id}/message/ (for updates)
        result = self._make_request('PUT', f'campaign/create/{campaign_id}/message/', data=data)
        if result['success']:
            return result
        
        # Second try: PATCH to campaign/create/{id}/message/
        if result.get('status_code') == 405:
            result = self._make_request('PATCH', f'campaign/create/{campaign_id}/message/', data=data)
            if result['success']:
                return result
        
        # Third try: POST to campaign/create/{id}/message/ (for new campaigns)
        if result.get('status_code') == 405:
            result = self._make_request('POST', f'campaign/create/{campaign_id}/message/', data=data)
            if result['success']:
                return result
        
        # Fourth try: PUT to campaign/{id}/message/ (alternative endpoint)
        if result.get('status_code') == 405:
            result = self._make_request('PUT', f'campaign/{campaign_id}/message/', data=data)
            if result['success']:
                return result
        
        # If all fail, return the last error
        return result
    
    def delete_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Delete a campaign"""
        return self._make_request('DELETE', f'campaign/{campaign_id}/')
    
    def get_campaign_details(self, campaign_id: int, page: Optional[int] = None) -> Dict[str, Any]:
        """Get campaign details (contact list)"""
        params = {'page': page} if page else None
        return self._make_request('GET', f'campaign-detail/{campaign_id}/', params=params)
    
    def run_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Run/execute a campaign immediately"""
        # According to TingTing API docs: run-campaign/{campaign_id}/
        # If schedule time is not given, campaign launches immediately
        # The API doesn't show sample input, so try POST without body and without Content-Type
        try:
            url = f"{self.base_url}/run-campaign/{campaign_id}/"
            
            # Prepare headers without Content-Type for this endpoint
            request_headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/json'
            }
            
            print(f"[TingTing API] Request: POST {url}")
            print(f"[TingTing API] Headers: {request_headers}")
            print(f"[TingTing API] Request Body: (no body)")
            
            # Send POST request without body
            response = requests.post(url, headers=request_headers, timeout=30)
            
            print(f"[TingTing API] Response Status: {response.status_code}")
            try:
                response_data = response.json()
                print(f"[TingTing API] Response Body: {response_data}")
            except ValueError:
                response_text = response.text[:500] if response.text else "No response body"
                print(f"[TingTing API] Response Body (non-JSON): {response_text}")
            
            if response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                    return {'success': True, 'data': response_data}
                except ValueError:
                    return {'success': True, 'data': {'message': 'Operation successful'}}
            else:
                error_msg = f'API returned status {response.status_code}'
                try:
                    error_data = response.json()
                    print(f"[TingTing API] ERROR Response: {error_data}")
                    error_msg = error_data.get('message', error_data.get('error', error_msg))
                except ValueError:
                    error_text = response.text or error_msg
                    print(f"[TingTing API] ERROR Response (non-JSON): {error_text}")
                    error_msg = error_text
                
                return {'success': False, 'error': error_msg, 'status_code': response.status_code}
                
        except requests.exceptions.Timeout:
            print(f"[TingTing API] ERROR: Timeout for run-campaign/{campaign_id}/")
            return {'success': False, 'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            print(f"[TingTing API] ERROR: Request error for run-campaign/{campaign_id}/: {str(e)}")
            return {'success': False, 'error': f'Request failed: {str(e)}'}
        except Exception as e:
            print(f"[TingTing API] ERROR: Unexpected error calling run-campaign/{campaign_id}/: {str(e)}")
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def download_report(self, campaign_id: int) -> Dict[str, Any]:
        """Download campaign report"""
        try:
            url = f"{self.base_url}/download/report/{campaign_id}/"
            response = requests.get(url, headers=self.headers, timeout=60, stream=True)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': {
                        'content': response.content,
                        'content_type': response.headers.get('Content-Type', 'text/csv'),
                        'filename': f'campaign_{campaign_id}_report.csv'
                    }
                }
            else:
                return {'success': False, 'error': f'Failed to download report: {response.status_code}'}
        except Exception as e:
            print(f"[TingTing API] ERROR: Error downloading report for campaign {campaign_id}: {str(e)}")
            return {'success': False, 'error': f'Error downloading report: {str(e)}'}
    
    # Contacts
    def add_contact(self, campaign_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add individual contact to campaign"""
        return self._make_request('POST', f'campaign/{campaign_id}/add-contact/', data=data)
    
    def add_bulk_contacts(self, campaign_id: int, file_path: str, file_content: bytes) -> Dict[str, Any]:
        """Add bulk contacts to campaign via file upload"""
        try:
            url = f"{self.base_url}/campaign/create/{campaign_id}/detail/"
            
            # Prepare files for multipart/form-data
            files = {'bulk_file': (file_path, file_content)}
            
            # Make POST request with file
            response = requests.post(
                url,
                headers={'Authorization': f'Bearer {self.api_key}'},
                files=files,
                timeout=120  # 2 minutes for file upload
            )
            
            if response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                    return {'success': True, 'data': response_data}
                except ValueError:
                    return {'success': True, 'data': {'message': 'File uploaded successfully'}}
            else:
                error_msg = f'API returned status {response.status_code}'
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_data.get('error', error_msg))
                except ValueError:
                    error_msg = response.text or error_msg
                
                return {'success': False, 'error': error_msg, 'status_code': response.status_code}
                
        except requests.exceptions.Timeout:
            print(f"[TingTing API] ERROR: Timeout for bulk contacts upload")
            return {'success': False, 'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            print(f"[TingTing API] ERROR: Request error for bulk contacts: {str(e)}")
            return {'success': False, 'error': f'Request failed: {str(e)}'}
        except Exception as e:
            print(f"[TingTing API] ERROR: Unexpected error uploading bulk contacts: {str(e)}")
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def delete_contact(self, contact_id: int) -> Dict[str, Any]:
        """Delete a contact"""
        return self._make_request('DELETE', f'phone-number/delete/{contact_id}/')
    
    def get_contact_info(self, contact_id: int) -> Dict[str, Any]:
        """Get contact information"""
        return self._make_request('GET', f'phone-number/{contact_id}/')
    
    def update_contact_attributes(self, contact_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update contact attributes"""
        return self._make_request('PATCH', f'phone-number/{contact_id}/attribute/', data=data)
    
    def update_contact(self, contact_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update contact"""
        return self._make_request('POST', f'phone-number/{contact_id}/', data=data)
    
    # Testing
    def test_voice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Test voice synthesis"""
        return self._make_request('POST', 'campaign/test-voice/', data=data)
    
    def demo_call(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a demo call"""
        return self._make_request('POST', 'campaign/demo-call/', data=data)


# Singleton instance
tingting_service = TingTingService()

