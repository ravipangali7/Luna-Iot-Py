"""
Authentication Decorators
Handles authentication and authorization decorators
"""
from functools import wraps
from django.http import JsonResponse
from api_common.utils.response_utils import error_response
from api_common.constants.api_constants import ERROR_MESSAGES


def require_auth(view_func):
    """
    Decorator to require authentication
    Checks if user is authenticated via middleware
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return error_response(
                message='Authentication required',
                status_code=401
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def require_role(allowed_roles):
    """
    Decorator to require specific roles
    Args:
        allowed_roles: List of allowed role names
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return error_response(
                    message='Authentication required',
                    status_code=401
                )
            
            user_role = getattr(request.user, 'role', None)
            if not user_role or user_role.name not in allowed_roles:
                return error_response(
                    message='Access denied. Insufficient permissions',
                    status_code=403
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_super_admin(view_func):
    """
    Decorator to require Super Admin role
    """
    return require_role(['Super Admin'])(view_func)


def require_dealer_or_admin(view_func):
    """
    Decorator to require Dealer or Super Admin role
    """
    return require_role(['Super Admin', 'Dealer'])(view_func)