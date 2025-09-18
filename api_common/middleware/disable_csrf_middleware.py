"""
Disable CSRF middleware for API endpoints
"""
from django.utils.deprecation import MiddlewareMixin


class DisableCSRFMiddleware(MiddlewareMixin):
    """
    Middleware to disable CSRF protection for API endpoints
    """
    
    def process_request(self, request):
        # Disable CSRF for all API requests
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None