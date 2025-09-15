"""
CORS Middleware
Handles Cross-Origin Resource Sharing
Matches Node.js cors_middleware.js functionality
"""
from django.utils.deprecation import MiddlewareMixin


class CorsMiddleware(MiddlewareMixin):
    """
    Middleware to handle CORS headers
    Matches Node.js corsMiddleware functionality
    """
    
    def process_response(self, request, response):
        # Set CORS headers
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, Authorization, x-phone, x-token'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        
        # Handle preflight OPTIONS requests
        if request.method == 'OPTIONS':
            response.status_code = 200
            
        return response