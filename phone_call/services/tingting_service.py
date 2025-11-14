"""
TingTing API Service
Handles all API calls to TingTing telephony service
"""
import requests
import logging
import re
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
    
    def add_voice_assistance(self, campaign_id: int, voice_id: int, category: str = "Text", message: Optional[str] = None) -> Dict[str, Any]:
        """Add voice assistance to a campaign"""
        data = {
            "voice": voice_id,  # Integer, not dict
            "category": category
        }
        # When category is "Text", message is required
        if category == "Text" and message:
            data["message"] = message
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
    
    def instant_launch_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Launch campaign immediately by clearing schedule first"""
        try:
            # Get current campaign to save schedule
            campaign_result = self.get_campaign(campaign_id)
            if not campaign_result['success']:
                return campaign_result
            
            campaign_data = campaign_result.get('data', {})
            original_schedule = campaign_data.get('schedule')
            
            # Clear schedule temporarily to force immediate launch
            if original_schedule:
                print(f"[Instant Launch] Clearing schedule for immediate launch: original_schedule={original_schedule}")
                update_result = self.update_campaign(campaign_id, {'schedule': None})
                if not update_result['success']:
                    print(f"[Instant Launch] Warning: Failed to clear schedule: {update_result.get('error')}")
                    # Continue anyway - try to run
            
            # Run campaign (will launch immediately since schedule is cleared)
            result = self.run_campaign(campaign_id)
            
            # Note: We don't restore the schedule because the campaign has already started
            # The user can reschedule if needed
            
            return result
            
        except Exception as e:
            print(f"[Instant Launch] ERROR: Unexpected error in instant launch: {str(e)}")
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
    
    def _normalize_message(self, message: str) -> str:
        """
        Aggressively normalize message for TingTing API compatibility.
        Removes multiple spaces, special characters, and formatting issues.
        
        Args:
            message: Original message string
            
        Returns:
            Normalized message string with all formatting issues fixed
        """
        if not isinstance(message, str):
            message = str(message)
        
        # Step 1: Replace newlines and carriage returns with spaces
        normalized = message.replace('\n', ' ').replace('\r', ' ')
        
        # Step 2: Replace problematic special characters
        # Replace pipe characters with single Nepali period
        normalized = normalized.replace('|', '।')
        
        # Step 3: Remove double punctuation marks
        normalized = re.sub(r'।+', '।', normalized)  # Consecutive Nepali periods
        normalized = re.sub(r'\.+', '.', normalized)  # Consecutive regular periods
        normalized = re.sub(r',+', ',', normalized)  # Consecutive commas
        
        # Step 4: Normalize ALL Unicode whitespace characters to single regular space
        # This catches regular spaces, non-breaking spaces, tabs, and all other Unicode whitespace
        normalized = re.sub(r'[\s\u00A0\u1680\u2000-\u200B\u202F\u205F\u3000\uFEFF]+', ' ', normalized)
        
        # Step 5: Apply regex again to ensure no multiple spaces remain
        normalized = re.sub(r' +', ' ', normalized)
        
        # Step 6: Trim whitespace from beginning and end
        normalized = normalized.strip()
        
        # Step 7: Remove any remaining control characters (except common punctuation)
        normalized = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', normalized)
        
        # Step 8: Clean up spacing around punctuation (before final whitespace normalization)
        # Remove spaces before punctuation
        normalized = re.sub(r'\s+([।,\.!?])', r'\1', normalized)
        # Ensure single space after punctuation (if not at end and not already followed by space)
        normalized = re.sub(r'([।,\.!?])([^\s।,\.!?])', r'\1 \2', normalized)
        
        # Step 9: Final aggressive whitespace cleanup - MUST be last step
        # Replace ALL whitespace (including any introduced by punctuation fixes) with single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Step 10: Final trim
        normalized = normalized.strip()
        
        # Step 11: One more pass to ensure absolutely no multiple spaces remain
        # This is a safety check after all transformations
        while '  ' in normalized:
            normalized = normalized.replace('  ', ' ')
        normalized = normalized.strip()
        
        # Step 12: Final validation - ensure no multiple spaces (using regex one more time)
        normalized = re.sub(r' +', ' ', normalized).strip()
        
        return normalized
    
    # Testing
    def test_voice(self, campaign_id: int, voice_input: int, message: str) -> Dict[str, Any]:
        """Test voice synthesis"""
        # Store original message for logging
        original_message = message
        
        # Pre-validation: Check if campaign exists
        print(f"[TingTing API] Pre-validation: Checking campaign {campaign_id} exists...")
        campaign_result = self.get_campaign(campaign_id)
        if not campaign_result.get('success'):
            return {
                'success': False,
                'error': f'Campaign {campaign_id} not found or not accessible',
                'status_code': 404
            }
        
        campaign_data = campaign_result.get('data', {})
        print(f"[TingTing API] Campaign found: ID={campaign_id}, Status={campaign_data.get('status', 'unknown')}")
        
        # Normalize message: ensure it's a string and handle encoding
        if not isinstance(message, str):
            message = str(message)
        
        # Ensure UTF-8 encoding
        try:
            message = message.encode('utf-8').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            # If encoding fails, try to fix it
            message = message.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        
        # Apply aggressive normalization BEFORE first request
        # This ensures the message is clean from the start
        normalized_message = self._normalize_message(message)
        
        # Validate normalized message
        if not normalized_message or not normalized_message.strip():
            return {
                'success': False,
                'error': 'Message is empty after normalization',
                'status_code': 400
            }
        
        # Check if normalization changed the message
        if normalized_message != message:
            print(f"[TingTing API] Message normalized: {len(message)} chars -> {len(normalized_message)} chars")
            print(f"[TingTing API] Original (first 100): {message[:100]}")
            print(f"[TingTing API] Normalized (first 100): {normalized_message[:100]}")
        
        # Use normalized message for the request
        message = normalized_message
        
        # Use the correct endpoint from documentation: test-speak/riri/<campaign_id>/
        endpoint = f'test-speak/riri/{campaign_id}/'
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Try multiple request formats to find what works
        request_formats = [
            {
                'name': 'JSON with charset',
                'headers': {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json; charset=utf-8',
                    'Accept': 'application/json'
                },
                'data': {
                    "voice_input": voice_input,
                    "message": message
                }
            },
            {
                'name': 'JSON without charset',
                'headers': {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                'data': {
                    "voice_input": voice_input,
                    "message": message
                }
            },
            {
                'name': 'JSON with string voice_input',
                'headers': {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                'data': {
                    "voice_input": str(voice_input),
                    "message": message
                }
            },
        ]
        
        last_error = None
        for req_format in request_formats:
        
            # Log request details (mask sensitive data)
            log_headers = req_format['headers'].copy()
            if 'Authorization' in log_headers:
                auth_header = log_headers['Authorization']
                if 'Bearer' in auth_header:
                    token = auth_header.split('Bearer ')[1]
                    masked_token = token[:10] + '...' + token[-5:] if len(token) > 15 else '***'
                    log_headers['Authorization'] = f'Bearer {masked_token}'
            
            print(f"[TingTing API] Test Voice - Trying format: {req_format['name']}")
            print(f"[TingTing API] Endpoint: {endpoint}")
            print(f"[TingTing API] Request: POST {url}")
            print(f"[TingTing API] Headers: {log_headers}")
            print(f"[TingTing API] Request Body: {req_format['data']}")
            print(f"[TingTing API] Message length: {len(message)} chars")
            
            try:
                # Make POST request
                response = requests.post(
                    url, 
                    headers=req_format['headers'], 
                    json=req_format['data'], 
                    timeout=30,
                    allow_redirects=True
                )
                
                print(f"[TingTing API] Response Status: {response.status_code}")
                print(f"[TingTing API] Response Headers: {dict(response.headers)}")
            
                # Check if successful
                if response.status_code in [200, 201]:
                    try:
                        response_data = response.json()
                        print(f"[TingTing API] SUCCESS! Response Body (JSON): {response_data}")
                    except ValueError:
                        # Response might be plain text URL (as per documentation)
                        response_text = response.text.strip()
                        print(f"[TingTing API] SUCCESS! Response Body (plain text): {response_text[:200]}")
                        response_data = response_text
                    
                    # Handle different response formats
                    # According to docs, it returns: "https://riritwo.prixacdn.net/output/..."
                    audio_url = None
                    if isinstance(response_data, str):
                        # Direct string URL (as per documentation)
                        audio_url = response_data.strip().strip('"')  # Remove quotes if present
                    elif isinstance(response_data, dict):
                        # JSON object - try multiple possible fields
                        audio_url = (response_data.get('url') or 
                                    response_data.get('audio_url') or 
                                    response_data.get('audio') or 
                                    response_data.get('file_url'))
                    
                    if audio_url and (audio_url.startswith('http://') or audio_url.startswith('https://')):
                        print(f"[TingTing API] Success with format: {req_format['name']}")
                        return {
                            'success': True,
                            'data': audio_url
                        }
                    else:
                        # Return the response as-is if we can't extract URL
                        print(f"[TingTing API] Success with format: {req_format['name']} (no URL extracted)")
                        return {
                            'success': True,
                            'data': response_data
                        }
                
                # Handle errors
                elif response.status_code == 400:
                    # Bad request - endpoint exists but request is invalid
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('message', error_data.get('error', f'Bad request: {response.status_code}'))
                        print(f"[TingTing API] ERROR Response (400) with format {req_format['name']}: {error_data}")
                        # Don't try other formats for 400 - the endpoint exists but request is wrong
                        return {
                            'success': False,
                            'error': error_msg,
                            'status_code': response.status_code
                        }
                    except ValueError:
                        error_text = response.text[:500] if response.text else "Bad request"
                        print(f"[TingTing API] ERROR Response (400, non-JSON) with format {req_format['name']}: {error_text}")
                        return {
                            'success': False,
                            'error': error_text,
                            'status_code': response.status_code
                        }
                
                elif response.status_code == 500:
                    # Server error - try next format
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('message', error_data.get('error', f'Status {response.status_code}'))
                        print(f"[TingTing API] ERROR Response (500) with format {req_format['name']}: {error_msg}")
                    except ValueError:
                        # Parse HTML error response for any useful information
                        error_html = response.text
                        print(f"[TingTing API] ERROR Response (500, HTML) with format {req_format['name']}")
                        print(f"[TingTing API] HTML Response (first 500 chars): {error_html[:500]}")
                        
                        # Try to extract any error message from HTML
                        title_match = re.search(r'<title>(.*?)</title>', error_html, re.IGNORECASE)
                        if title_match:
                            print(f"[TingTing API] HTML Error Title: {title_match.group(1)}")
                        
                        # Check for any error details in the HTML
                        body_match = re.search(r'<body[^>]*>(.*?)</body>', error_html, re.IGNORECASE | re.DOTALL)
                        if body_match:
                            body_text = re.sub(r'<[^>]+>', '', body_match.group(1))
                            print(f"[TingTing API] HTML Body Text: {body_text[:200]}")
                    
                    last_error = f'Format {req_format["name"]} failed with 500 error'
                    continue  # Try next format
                
                else:
                    # Other errors (404, etc.) - try next format
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('message', error_data.get('error', f'Status {response.status_code}'))
                        print(f"[TingTing API] ERROR Response ({response.status_code}) with format {req_format['name']}: {error_msg}")
                    except ValueError:
                        error_text = response.text[:500] if response.text else f"Status {response.status_code}"
                        print(f"[TingTing API] ERROR Response ({response.status_code}, non-JSON) with format {req_format['name']}: {error_text}")
                    
                    last_error = f'Format {req_format["name"]} failed with status {response.status_code}'
                    continue  # Try next format
                    
            except requests.exceptions.RequestException as e:
                print(f"[TingTing API] Request error with format {req_format['name']}: {str(e)}")
                last_error = f'Format {req_format["name"]} request failed: {str(e)}'
                continue  # Try next format
            except Exception as e:
                print(f"[TingTing API] Unexpected error with format {req_format['name']}: {str(e)}")
                import traceback
                print(f"[TingTing API] Traceback: {traceback.format_exc()}")
                last_error = f'Format {req_format["name"]} unexpected error: {str(e)}'
                continue  # Try next format
        
        # If all formats failed, return error
        print(f"[TingTing API] All request formats failed. Last error: {last_error}")
        return {
            'success': False,
            'error': f'All request formats failed. The TingTing API returned 500 errors for all formats. This might indicate: (1) Campaign {campaign_id} is not in the correct state, (2) Voice ID {voice_input} is invalid for this campaign, (3) The API endpoint requires additional setup, or (4) There is an issue with the TingTing API service. Please verify the campaign exists and is accessible, and that the voice ID is valid.',
            'status_code': 500
        }
    
    def demo_call(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a demo call"""
        return self._make_request('POST', 'campaign/demo-call/', data=data)


# Singleton instance
tingting_service = TingTingService()

