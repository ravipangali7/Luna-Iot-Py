"""
Validation Decorators
Handles field validation decorators
"""
from functools import wraps
from api_common.utils.response_utils import error_response
from api_common.utils.validation_utils import validate_required_fields


def validate_fields(required_fields):
    """
    Decorator to validate required fields in request data
    Args:
        required_fields: List of required field names
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get data from request
            if hasattr(request, 'data'):
                data = request.data
            else:
                data = request.POST if request.method == 'POST' else request.GET
            
            # Validate required fields
            validation_result = validate_required_fields(data, required_fields)
            if not validation_result['is_valid']:
                return error_response(
                    message=validation_result['message'],
                    status_code=400
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def validate_phone(view_func):
    """
    Decorator to validate phone number format
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from api_common.utils.validation_utils import validate_phone_number
        
        phone = request.data.get('phone') if hasattr(request, 'data') else request.POST.get('phone')
        if phone and not validate_phone_number(phone):
            return error_response(
                message='Invalid phone number format',
                status_code=400
            )
        
        return view_func(request, *args, **kwargs)
    return wrapper
