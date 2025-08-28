from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from .models import User

class TokenAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip authentication for public endpoints
        public_paths = [
            '/api/auth/send_registration_otp/',
            '/api/auth/verify_otp_and_register/',
            '/api/auth/login/',
            '/api/auth/resend_otp/',
            '/api/auth/send_forgot_password_otp/',
            '/api/auth/verify_forgot_password_otp/',
            '/api/auth/reset_password/',
            '/api/popup/active/',
        ]
        
        if request.path in public_paths:
            request.user = AnonymousUser()
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