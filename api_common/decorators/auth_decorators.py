"""
Authentication Decorators
Handles authentication and authorization decorators
"""
from functools import wraps
from django.http import JsonResponse
from api_common.utils.response_utils import error_response
from api_common.constants.api_constants import ERROR_MESSAGES
from core.models import InstituteModule, Module


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
            # Debug logging for vehicle tag history endpoint
            if request.path and '/api/vehicle-tag/history/' in request.path:
                print(f"[require_role] Checking authentication for {request.path}")
                print(f"[require_role] Has user attr: {hasattr(request, 'user')}")
                if hasattr(request, 'user'):
                    print(f"[require_role] User: {request.user}, is_authenticated: {request.user.is_authenticated}")
                else:
                    print(f"[require_role] User not set on request")
            
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                if request.path and '/api/vehicle-tag/history/' in request.path:
                    print(f"[require_role] Authentication failed - returning 401")
                return error_response(
                    message='Authentication required',
                    status_code=401
                )
            
            # Check if user has any of the allowed roles
            user_groups = request.user.groups.all()
            user_role_names = [group.name for group in user_groups]
            
            if not any(role_name in allowed_roles for role_name in user_role_names):
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


def require_school_module_access(model_class=None, id_param_name='id'):
    """
    Decorator to require Super Admin role OR institute module access for school operations
    
    Args:
        model_class: Optional model class to fetch record for PUT/DELETE operations
                    Should have 'institute' field (ForeignKey) or method to get institute_id
        id_param_name: Name of the URL parameter containing the record ID (default: 'id')
    
    For create operations (POST): extracts institute_id from request.data['institute']
    For update/delete operations (PUT/DELETE): fetches record using model_class and extracts institute_id
    For SchoolParent: checks institutes through school_buses relationship
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return error_response(
                    message='Authentication required',
                    status_code=401
                )
            
            # Check if user is Super Admin - always allow
            user_groups = request.user.groups.all()
            user_role_names = [group.name for group in user_groups]
            is_super_admin = 'Super Admin' in user_role_names
            
            if is_super_admin:
                return view_func(request, *args, **kwargs)
            
            # For non-Super Admin users, check institute module access
            try:
                # Get the school module
                school_module = Module.objects.get(slug='school')
            except Module.DoesNotExist:
                return error_response(
                    message='School module not found',
                    status_code=500
                )
            
            # Get institute_id(s) based on HTTP method
            institute_ids = []
            
            if request.method == 'POST':
                # For create operations, get institute_id from request.data
                institute_id = request.data.get('institute')
                if institute_id:
                    if isinstance(institute_id, dict):
                        institute_id = institute_id.get('id') or institute_id.get('pk')
                    elif hasattr(institute_id, 'id'):
                        institute_id = institute_id.id
                    if institute_id:
                        institute_ids = [institute_id]
                else:
                    # Check for school_buses (for SchoolParent create)
                    school_bus_ids = request.data.get('school_buses', [])
                    if school_bus_ids:
                        from school.models import SchoolBus
                        try:
                            school_buses = SchoolBus.objects.filter(id__in=school_bus_ids).select_related('institute')
                            institute_ids = list(set([bus.institute.id for bus in school_buses if bus.institute]))
                        except Exception:
                            pass
            elif request.method in ['PUT', 'DELETE'] and model_class:
                # For update/delete operations, get record and extract institute_id
                record_id = kwargs.get(id_param_name) or kwargs.get('bus_id') or kwargs.get('parent_id') or kwargs.get('sms_id')
                if record_id:
                    try:
                        record = model_class.objects.get(id=record_id)
                        
                        # Check if record has direct institute field
                        if hasattr(record, 'institute'):
                            institute = record.institute
                            if institute:
                                institute_ids = [institute.id if hasattr(institute, 'id') else institute]
                        # For SchoolParent, check through school_buses
                        elif hasattr(record, 'school_buses'):
                            school_buses = record.school_buses.all()
                            institute_ids = list(set([bus.institute.id for bus in school_buses if hasattr(bus, 'institute')]))
                    except model_class.DoesNotExist:
                        # Record doesn't exist - let the view handle the 404
                        pass
            
            # Check if user has access to any of the institutes
            if institute_ids:
                has_access = InstituteModule.objects.filter(
                    module=school_module,
                    institute_id__in=institute_ids,
                    users=request.user
                ).exists()
                
                if not has_access:
                    return error_response(
                        message='Access denied. Insufficient permissions',
                        status_code=403
                    )
            else:
                # If no institute_id found and not Super Admin, deny access
                return error_response(
                    message='Access denied. Insufficient permissions',
                    status_code=403
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator