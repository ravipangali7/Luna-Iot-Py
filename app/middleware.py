from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from .models import User

class TokenAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip authentication for Django system paths
        system_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/__debug__/',
            '/favicon.ico',
        ]
        
        # Skip authentication for public API endpoints
        normalized = request.path.rstrip('/') or '/'
        public_paths = [
            '/api/auth/send_registration_otp',
            '/api/auth/verify_otp_and_register',
            '/api/auth/login',
            '/api/auth/resend_otp',
            '/api/auth/send_forgot_password_otp',
            '/api/auth/verify_forgot_password_otp',
            '/api/auth/reset_password',
            '/api/popup/active',
        ]
        
        # Check if it's a system path (skip our auth)
        for system_path in system_paths:
            if request.path.startswith(system_path):
                return None
        
        # Check if it's a public API path (skip our auth)
        if normalized in public_paths:
            request.user = AnonymousUser()
            return None
        
        # Only apply our custom auth to API requests
        if not request.path.startswith('/api/'):
            return None
        
        phone = request.headers.get('x-phone')
        token = request.headers.get('x-token')
        
        if phone and token:
            try:
                user = User.objects.get(phone=phone, token=token, status='ACTIVE')
                request.user = user
            except User.DoesNotExist:
                request.user = AnonymousUser()
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid token or phone'
                }, status=777)
        else:
            request.user = AnonymousUser()
            return JsonResponse({
                'success': False,
                'message': 'Phone and token required'
            }, status=401)
        
        return None