# luna_iot_py/app/authentication.py
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import AnonymousUser
from .models import User

class HeaderTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if not request.path.startswith('/api/'):
            return None  # ignore non-API
        # Public endpoints can skip, let permissions handle AllowAny
        public = {
            '/api/auth/send_registration_otp',
            '/api/auth/verify_otp_and_register',
            '/api/auth/login',
            '/api/auth/resend_otp',
            '/api/auth/send_forgot_password_otp',
            '/api/auth/verify_forgot_password_otp',
            '/api/auth/reset_password',
            '/api/popup/active',
        }
        normalized = request.path.rstrip('/') or '/'
        if normalized in public:
            return (AnonymousUser(), None)

        phone = request.headers.get('x-phone')
        token = request.headers.get('x-token')
        if not phone or not token:
            raise AuthenticationFailed('Phone and token required')

        try:
            user = User.objects.get(phone=phone, token=token, status='ACTIVE')
        except User.DoesNotExist:
            # Use 401-like semantics so client can re-auth
            raise AuthenticationFailed('Invalid token or phone')

        return (user, None)