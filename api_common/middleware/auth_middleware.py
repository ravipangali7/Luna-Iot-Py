"""
Authentication Middleware
Handles token verification using x-phone and x-token headers
Matches Node.js auth_middleware.js functionality
"""
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from core.models.user import User
from api_common.utils.response_utils import error_response
from api_common.constants.api_constants import ERROR_MESSAGES
 

class AuthMiddleware(MiddlewareMixin):
    """
    Middleware to verify authentication token
    Matches Node.js AuthMiddleware.verifyToken functionality
    """
    
    def process_request(self, request):
        # Skip authentication for public routes
        public_paths = [
            '/api/core/auth/login',
            '/api/core/auth/register/send-otp',
            '/api/core/auth/register/verify-otp',
            '/api/core/auth/register/resend-otp',
            '/api/core/auth/forgot-password/send-otp',
            '/api/core/auth/forgot-password/verify-otp',
            '/api/core/auth/forgot-password/reset-password',
            '/api/core/auth/biometric-login',  # Public biometric login endpoint
            '/api/health/blood-donation',  # Public blood donation endpoints
            '/api/shared/popup/active',  # Public popup endpoint
        ]
        
        # Skip authentication for public share-track routes (viewing shared links)
        if request.path.startswith('/api/fleet/share-track/token/'):
            return None
        
        # Skip authentication for public radar token routes
        if request.path.startswith('/api/alert-system/alert-radar/token/'):
            return None
        
        # Skip authentication for public alert history by radar routes  
        if request.path.startswith('/api/alert-system/alert-history/by-radar/'):
            return None
        
        # Skip authentication for alert history create endpoint (called by Node)
        if request.path.startswith('/api/alert-system/alert-history/create/') and request.method == 'POST':
            return None
        
        # Skip authentication for vehicle tag alert endpoints (public access)
        if request.path.startswith('/api/vehicle-tag/alert/'):
            return None
        
        # Skip authentication for vehicle tag public endpoints (public access for alert page)
        import re
        # Match any VTID format followed by: /, /latest-alert/, or /qr/
        # Examples: /api/vehicle-tag/VTID84/, /api/vehicle-tag/VTID84/latest-alert/, /api/vehicle-tag/VTID84/qr/
        if (re.match(r'^/api/vehicle-tag/[^/]+/(latest-alert/|qr/)$', request.path) or
            re.match(r'^/api/vehicle-tag/[^/]+/$', request.path)):
            return None
        
        # Skip authentication for media files
        if request.path.startswith('/media/'):
            return None

        # Skip authentication for public short-link resolver endpoint
        if request.path.startswith('/api/shared/short-links/'):
            return None
            
        # Skip authentication for health blood donation endpoints
        if request.path.startswith('/api/health/blood-donation'):
            return None
        
        # Skip authentication for Django admin interface
        if request.path.startswith('/admin'):
            return None
        if request.path.startswith('/admin/'):
            return None
        
        # Skip authentication for specific device endpoints (Node.js GT06 handler)
        if request.path.startswith('/api/device/status/') and request.method == 'POST':
            return None
        if request.path.startswith('/api/device/location/') and request.method == 'POST':
            return None
        
        if request.path in public_paths:
            return None
            
        # Extract phone and token from headers
        phone = request.META.get('HTTP_X_PHONE')
        token = request.META.get('HTTP_X_TOKEN')
        
        if not phone or not token:
            return error_response( 
                message='Phone and token required',
                status_code=401
            )
        
        try:
            # Find user by phone first, then verify token
            
            # First check if any users exist
            user_count = User.objects.count()
            
            # List all users for debugging
            all_users = User.objects.all()[:5]  # Get first 5 users
            
            # Find user by phone
            user = User.objects.get(phone=phone)
            
            # Check if token matches
            if user.token != token:
                print(f"Auth Middleware: Token mismatch - user token: {user.token}, expected: {token}")
                return error_response(
                    message='Invalid token',
                    status_code=401
                )
            
            if not user.is_active:
                print(f"Auth Middleware: User is not active")
                return error_response(
                    message='User account is not active',
                    status_code=777
                )
            
            # Add user to request
            request.user = user
            return None
            
        except User.DoesNotExist:
            print(f"Auth Middleware: User not found with phone: {phone}")
            return error_response(
                message='User matching query does not exist.',
                status_code=404
            )
            
        except Exception as e:
            print(f"Auth Middleware: Exception occurred: {str(e)}")
            import traceback
            traceback.print_exc()
            return error_response(
                message='Authentication error',
                status_code=500
            )
