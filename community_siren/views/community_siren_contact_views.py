"""
Community Siren Contact Views
Handles community siren contact management endpoints
"""
from rest_framework.decorators import api_view
from community_siren.models import CommunitySirenContact
from community_siren.serializers import (
    CommunitySirenContactSerializer,
    CommunitySirenContactCreateSerializer,
    CommunitySirenContactUpdateSerializer,
    CommunitySirenContactListSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth
from api_common.exceptions.api_exceptions import NotFoundError
from core.models import Module, InstituteModule
from functools import wraps


def require_community_siren_module_access(model_class=None, id_param_name='id'):
    """Decorator to require Super Admin role OR institute module access for community-siren operations"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return error_response(message='Authentication required', status_code=401)
            
            user_groups = request.user.groups.all()
            user_role_names = [group.name for group in user_groups]
            is_super_admin = 'Super Admin' in user_role_names
            
            if is_super_admin:
                return view_func(request, *args, **kwargs)
            
            try:
                community_siren_module = Module.objects.get(slug='community-siren')
            except Module.DoesNotExist:
                return error_response(message='Community siren module not found', status_code=500)
            
            institute_ids = []
            if request.method == 'POST':
                institute_id = request.data.get('institute')
                if institute_id:
                    if isinstance(institute_id, dict):
                        institute_id = institute_id.get('id') or institute_id.get('pk')
                    elif hasattr(institute_id, 'id'):
                        institute_id = institute_id.id
                    if institute_id:
                        institute_ids = [institute_id]
            elif request.method in ['PUT', 'DELETE'] and model_class:
                record_id = kwargs.get(id_param_name) or kwargs.get('contact_id')
                if record_id:
                    try:
                        record = model_class.objects.get(id=record_id)
                        if hasattr(record, 'institute'):
                            institute = record.institute
                            if institute:
                                institute_ids = [institute.id if hasattr(institute, 'id') else institute]
                    except model_class.DoesNotExist:
                        pass
            
            if institute_ids:
                has_access = InstituteModule.objects.filter(
                    module=community_siren_module,
                    institute_id__in=institute_ids,
                    users=request.user
                ).exists()
                if not has_access:
                    return error_response(message='Access denied. Insufficient permissions', status_code=403)
            else:
                return error_response(message='Access denied. Insufficient permissions', status_code=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


@api_view(['GET'])
@require_auth
@api_response
def get_all_community_siren_contacts(request):
    """Get all community siren contacts"""
    try:
        contacts = CommunitySirenContact.objects.select_related('institute').all().order_by('-created_at')
        serializer = CommunitySirenContactListSerializer(contacts, many=True)
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Community siren contacts retrieved successfully')
        )
    except Exception as e:
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))


@api_view(['GET'])
@require_auth
@api_response
def get_community_siren_contact_by_id(request, contact_id):
    """Get community siren contact by ID"""
    try:
        try:
            contact = CommunitySirenContact.objects.select_related('institute').get(id=contact_id)
        except CommunitySirenContact.DoesNotExist:
            raise NotFoundError("Community siren contact not found")
        serializer = CommunitySirenContactSerializer(contact)
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Community siren contact retrieved successfully')
        )
    except NotFoundError as e:
        return error_response(message=str(e), status_code=HTTP_STATUS['NOT_FOUND'])
    except Exception as e:
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))


@api_view(['GET'])
@require_auth
@api_response
def get_community_siren_contacts_by_institute(request, institute_id):
    """Get community siren contacts by institute"""
    try:
        contacts = CommunitySirenContact.objects.filter(institute_id=institute_id).order_by('-created_at')
        serializer = CommunitySirenContactListSerializer(contacts, many=True)
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Community siren contacts retrieved successfully')
        )
    except Exception as e:
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))


@api_view(['POST'])
@require_auth
@require_community_siren_module_access()
@api_response
def create_community_siren_contact(request):
    """Create new community siren contact"""
    try:
        serializer = CommunitySirenContactCreateSerializer(data=request.data)
        if serializer.is_valid():
            contact = serializer.save()
            response_serializer = CommunitySirenContactSerializer(contact)
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Community siren contact created successfully'),
                status_code=HTTP_STATUS['CREATED']
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except Exception as e:
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))


@api_view(['PUT'])
@require_auth
@require_community_siren_module_access(CommunitySirenContact, 'contact_id')
@api_response
def update_community_siren_contact(request, contact_id):
    """Update community siren contact"""
    try:
        try:
            contact = CommunitySirenContact.objects.get(id=contact_id)
        except CommunitySirenContact.DoesNotExist:
            raise NotFoundError("Community siren contact not found")
        serializer = CommunitySirenContactUpdateSerializer(contact, data=request.data)
        if serializer.is_valid():
            contact = serializer.save()
            response_serializer = CommunitySirenContactSerializer(contact)
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Community siren contact updated successfully')
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except NotFoundError as e:
        return error_response(message=str(e), status_code=HTTP_STATUS['NOT_FOUND'])
    except Exception as e:
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))


@api_view(['DELETE'])
@require_auth
@require_community_siren_module_access(CommunitySirenContact, 'contact_id')
@api_response
def delete_community_siren_contact(request, contact_id):
    """Delete community siren contact"""
    try:
        try:
            contact = CommunitySirenContact.objects.get(id=contact_id)
        except CommunitySirenContact.DoesNotExist:
            raise NotFoundError("Community siren contact not found")
        contact_name = contact.name
        contact.delete()
        return success_response(
            data={'id': contact_id},
            message=f"Community siren contact '{contact_name}' deleted successfully"
        )
    except NotFoundError as e:
        return error_response(message=str(e), status_code=HTTP_STATUS['NOT_FOUND'])
    except Exception as e:
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))
