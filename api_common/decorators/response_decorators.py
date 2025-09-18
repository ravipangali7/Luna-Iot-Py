"""
Response Decorators
Handles response formatting decorators
"""
from functools import wraps
from api_common.utils.response_utils import success_response, error_response


def api_response(view_func):
    """
    Decorator to handle API responses consistently
    Catches exceptions and formats responses
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            result = view_func(request, *args, **kwargs)
            
            # If result is already a JsonResponse, return it directly
            from django.http import JsonResponse
            if isinstance(result, JsonResponse):
                return result
            
            # If result is a dict, wrap it in success response
            if isinstance(result, dict):
                return success_response(data=result)
            
            # If result is a tuple (data, message, status_code)
            if isinstance(result, tuple) and len(result) == 3:
                data, message, status_code = result
                return success_response(data=data, message=message, status_code=status_code)
            
            # If result is a tuple (data, message)
            if isinstance(result, tuple) and len(result) == 2:
                data, message = result
                return success_response(data=data, message=message)
            
            # Default success response
            return success_response(data=result)
            
        except Exception as e:
            return error_response(
                message=str(e),
                status_code=500
            )
    return wrapper


def json_response(view_func):
    """
    Decorator to ensure JSON response
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        result = view_func(request, *args, **kwargs)
        
        # If result is already a JsonResponse, return it
        if hasattr(result, 'content_type') and 'application/json' in result.content_type:
            return result
        
        # Convert to JSON response
        return success_response(data=result)
    return wrapper
