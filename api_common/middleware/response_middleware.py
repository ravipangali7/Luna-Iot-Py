"""
Response Middleware
Handles global response formatting
"""
from django.utils.deprecation import MiddlewareMixin
from api_common.utils.response_utils import format_response


class ResponseMiddleware(MiddlewareMixin):
    """
    Middleware to format API responses consistently
    """
    
    def process_response(self, request, response):
        # Only process JSON responses
        if hasattr(response, 'content_type') and 'application/json' in response.content_type:
            # Response is already formatted by views
            pass
            
        return response
