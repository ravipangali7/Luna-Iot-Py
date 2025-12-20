"""
CORS Middleware
Handles Cross-Origin Resource Sharing
Matches Node.js cors_middleware.js functionality
"""
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


class CorsMiddleware(MiddlewareMixin):
    """
    Middleware to handle CORS headers
    Matches Node.js corsMiddleware functionality
    Ensures CORS headers are always added, even on errors
    """
    
    def process_response(self, request, response):
        # Get the origin from the request
        origin = request.META.get('HTTP_ORIGIN', '*')
        
        # If credentials are being sent, we must specify the exact origin (not *)
        # Otherwise, use * for simplicity
        if origin and origin != '*':
            # Allow specific origins (for development and production)
            allowed_origins = [
                'http://localhost:5173',
                'http://127.0.0.1:5173',
                'https://ios.mylunago.com',
                'https://www.mylunago.com',
                'https://mylunago.com',
            ]
            
            # Check if origin is in allowed list or contains localhost/127.0.0.1 (for dev)
            if origin in allowed_origins or 'localhost' in origin or '127.0.0.1' in origin:
                response['Access-Control-Allow-Origin'] = origin
            else:
                # For production, allow the origin if it's from mylunago.com domain
                if 'mylunago.com' in origin:
                    response['Access-Control-Allow-Origin'] = origin
                else:
                    response['Access-Control-Allow-Origin'] = '*'
        else:
            response['Access-Control-Allow-Origin'] = '*'
        
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, Authorization, x-phone, x-token'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
        response['Access-Control-Max-Age'] = '86400'  # 24 hours
        
        # Handle preflight OPTIONS requests
        if request.method == 'OPTIONS':
            response.status_code = 200
            response.content = b''
            
        return response
    
    def process_exception(self, request, exception):
        """
        Handle exceptions and ensure CORS headers are added even on errors
        """
        logger.error(f"Exception in request: {str(exception)}", exc_info=True)
        
        # Get the origin from the request
        origin = request.META.get('HTTP_ORIGIN', '*')
        
        # Return error response with CORS headers
        error_response = JsonResponse(
            {
                'success': False,
                'message': 'Internal server error',
                'data': {'error': str(exception)}
            },
            status=500
        )
        
        # Add CORS headers to error response (same logic as process_response)
        if origin and origin != '*':
            allowed_origins = [
                'http://localhost:5173',
                'http://127.0.0.1:5173',
                'https://ios.mylunago.com',
                'https://www.mylunago.com',
                'https://mylunago.com',
            ]
            
            if origin in allowed_origins or 'localhost' in origin or '127.0.0.1' in origin:
                error_response['Access-Control-Allow-Origin'] = origin
            elif 'mylunago.com' in origin:
                error_response['Access-Control-Allow-Origin'] = origin
            else:
                error_response['Access-Control-Allow-Origin'] = '*'
        else:
            error_response['Access-Control-Allow-Origin'] = '*'
        
        error_response['Access-Control-Allow-Credentials'] = 'true'
        error_response['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, Authorization, x-phone, x-token'
        error_response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
        
        return error_response