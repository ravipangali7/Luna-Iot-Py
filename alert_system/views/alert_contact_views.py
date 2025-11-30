"""
Alert Contact Views
Handles alert contact management endpoints
"""
from rest_framework.decorators import api_view
from alert_system.models import AlertContact
from alert_system.serializers import (
    AlertContactSerializer,
    AlertContactCreateSerializer,
    AlertContactUpdateSerializer,
    AlertContactListSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError
from core.models import Module, InstituteModule


def require_alert_system_module_access(model_class=None, id_param_name='id'):
    """
    Decorator to require Super Admin role OR institute module access for alert-system operations
    
    Args:
        model_class: Optional model class to fetch record for PUT/DELETE operations
                    Should have 'institute' field (ForeignKey)
        id_param_name: Name of the URL parameter containing the record ID (default: 'id')
    
    For create operations (POST): extracts institute_id from request.data['institute']
    For update/delete operations (PUT/DELETE): fetches record using model_class and extracts institute_id
    """
    def decorator(view_func):
        from functools import wraps
        from api_common.utils.response_utils import error_response
        
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
                # Get the alert-system module
                alert_system_module = Module.objects.get(slug='alert-system')
            except Module.DoesNotExist:
                return error_response(
                    message='Alert system module not found',
                    status_code=500
                )
            
            # Get institute_id(s) based on HTTP method
            institute_ids = []
            
            if request.method == 'POST':
                # For create operations, get institute_id from request.data
                institute_id = request.data.get('institute')
                if institute_id:
                    # Handle different formats: number, dict, or object
                    if isinstance(institute_id, (int, float)):
                        # Already a number
                        institute_ids = [int(institute_id)]
                    elif isinstance(institute_id, dict):
                        # Dictionary format
                        extracted_id = institute_id.get('id') or institute_id.get('pk')
                        if extracted_id:
                            institute_ids = [int(extracted_id)]
                    elif hasattr(institute_id, 'id'):
                        # Object with id attribute
                        institute_ids = [int(institute_id.id)]
                    elif isinstance(institute_id, str) and institute_id.isdigit():
                        # String representation of number
                        institute_ids = [int(institute_id)]
                    else:
                        # Try to convert to int directly
                        try:
                            institute_ids = [int(institute_id)]
                        except (ValueError, TypeError):
                            pass
            elif request.method in ['PUT', 'DELETE'] and model_class:
                # For update/delete operations, get record and extract institute_id
                record_id = kwargs.get(id_param_name) or kwargs.get('contact_id')
                if record_id:
                    try:
                        record = model_class.objects.get(id=record_id)
                        
                        # Check if record has direct institute field
                        if hasattr(record, 'institute'):
                            institute = record.institute
                            if institute:
                                institute_ids = [institute.id if hasattr(institute, 'id') else institute]
                    except model_class.DoesNotExist:
                        # Record doesn't exist - let the view handle the 404
                        pass
            
            # Check if user has access to any of the institutes
            if institute_ids:
                has_access = InstituteModule.objects.filter(
                    module=alert_system_module,
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


@api_view(['GET'])
@require_auth
@api_response
def get_all_alert_contacts(request):
    """Get all alert contacts"""
    try:
        contacts = AlertContact.objects.prefetch_related('alert_geofences', 'alert_types').select_related('institute').all().order_by('-created_at')
        serializer = AlertContactListSerializer(contacts, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert contacts retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_alert_contact_by_id(request, contact_id):
    """Get alert contact by ID"""
    try:
        try:
            contact = AlertContact.objects.prefetch_related('alert_geofences', 'alert_types').select_related('institute').get(id=contact_id)
        except AlertContact.DoesNotExist:
            raise NotFoundError("Alert contact not found")
        
        serializer = AlertContactSerializer(contact)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert contact retrieved successfully')
        )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_alert_contacts_by_institute(request, institute_id):
    """Get alert contacts by institute"""
    try:
        contacts = AlertContact.objects.prefetch_related('alert_geofences', 'alert_types').filter(institute_id=institute_id).order_by('-created_at')
        serializer = AlertContactListSerializer(contacts, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert contacts retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_alert_system_module_access(AlertContact, 'contact_id')
@api_response
def create_alert_contact(request):
    """Create new alert contact"""
    try:
        serializer = AlertContactCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            contact = serializer.save()
            response_serializer = AlertContactSerializer(contact)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Alert contact created successfully'),
                status_code=HTTP_STATUS['CREATED']
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['PUT'])
@require_alert_system_module_access(AlertContact, 'contact_id')
@api_response
def update_alert_contact(request, contact_id):
    """Update alert contact"""
    try:
        try:
            contact = AlertContact.objects.get(id=contact_id)
        except AlertContact.DoesNotExist:
            raise NotFoundError("Alert contact not found")
        
        serializer = AlertContactUpdateSerializer(contact, data=request.data)
        
        if serializer.is_valid():
            contact = serializer.save()
            response_serializer = AlertContactSerializer(contact)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Alert contact updated successfully')
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['DELETE'])
@require_alert_system_module_access(AlertContact, 'contact_id')
@api_response
def delete_alert_contact(request, contact_id):
    """Delete alert contact"""
    try:
        try:
            contact = AlertContact.objects.get(id=contact_id)
        except AlertContact.DoesNotExist:
            raise NotFoundError("Alert contact not found")
        
        contact_name = contact.name
        contact.delete()
        
        return success_response(
            data={'id': contact_id},
            message=f"Alert contact '{contact_name}' deleted successfully"
        )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )
