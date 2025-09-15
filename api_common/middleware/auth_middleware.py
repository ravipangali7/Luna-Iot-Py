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
            '/api/health/blood-donation',  # Public blood donation endpoints
            '/api/shared/popup/active',  # Public popup endpoint
        ]
        
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
            # Find user by phone and token
            user = User.objects.select_related('role').get(
                phone=phone,
                token=token
            )
            
            if user.status != 'ACTIVE':
                return error_response(
                    message='User account is not active',
                    status_code=777
                )
            
            # Add user to request
            request.user = user
            return None
            
        except User.DoesNotExist:
            return error_response(
                message='Invalid token or phone',
                status_code=777
            )
        except Exception as e:
            return error_response(
                message='Authentication error',
                status_code=500
            )
