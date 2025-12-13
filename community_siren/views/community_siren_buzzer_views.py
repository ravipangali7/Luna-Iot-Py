"""
Community Siren Buzzer Views
Handles community siren buzzer management endpoints
"""
from rest_framework.decorators import api_view
from community_siren.models import CommunitySirenBuzzer
from community_siren.serializers import (
    CommunitySirenBuzzerSerializer,
    CommunitySirenBuzzerCreateSerializer,
    CommunitySirenBuzzerUpdateSerializer,
    CommunitySirenBuzzerListSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth
from api_common.exceptions.api_exceptions import NotFoundError
from core.models import Module, InstituteModule
from functools import wraps


def require_community_siren_module_access(model_class=None, id_param_name='id'):
    """
    Decorator to require Super Admin role OR institute module access for community-siren operations
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
                # Get the community-siren module
                community_siren_module = Module.objects.get(slug='community-siren')
            except Module.DoesNotExist:
                return error_response(
                    message='Community siren module not found',
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
            elif request.method in ['PUT', 'DELETE'] and model_class:
                # For update/delete operations, get record and extract institute_id
                record_id = kwargs.get(id_param_name) or kwargs.get('buzzer_id')
                if record_id:
                    try:
                        record = model_class.objects.get(id=record_id)
                        if hasattr(record, 'institute'):
                            institute = record.institute
                            if institute:
                                institute_ids = [institute.id if hasattr(institute, 'id') else institute]
                    except model_class.DoesNotExist:
                        pass
            
            # Check if user has access to any of the institutes
            if institute_ids:
                has_access = InstituteModule.objects.filter(
                    module=community_siren_module,
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
def get_all_community_siren_buzzers(request):
    """Get all community siren buzzers"""
    try:
        buzzers = CommunitySirenBuzzer.objects.select_related('institute', 'device').all().order_by('-created_at')
        serializer = CommunitySirenBuzzerListSerializer(buzzers, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Community siren buzzers retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_community_siren_buzzer_by_id(request, buzzer_id):
    """Get community siren buzzer by ID"""
    try:
        try:
            buzzer = CommunitySirenBuzzer.objects.select_related('institute', 'device').get(id=buzzer_id)
        except CommunitySirenBuzzer.DoesNotExist:
            raise NotFoundError("Community siren buzzer not found")
        
        serializer = CommunitySirenBuzzerSerializer(buzzer)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Community siren buzzer retrieved successfully')
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
def get_community_siren_buzzers_by_institute(request, institute_id):
    """Get community siren buzzers by institute"""
    try:
        buzzers = CommunitySirenBuzzer.objects.select_related('device').filter(institute_id=institute_id).order_by('-created_at')
        serializer = CommunitySirenBuzzerListSerializer(buzzers, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Community siren buzzers retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_auth
@require_community_siren_module_access()
@api_response
def create_community_siren_buzzer(request):
    """Create new community siren buzzer"""
    try:
        serializer = CommunitySirenBuzzerCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            buzzer = serializer.save()
            response_serializer = CommunitySirenBuzzerSerializer(buzzer)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Community siren buzzer created successfully'),
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
@require_auth
@require_community_siren_module_access(CommunitySirenBuzzer, 'buzzer_id')
@api_response
def update_community_siren_buzzer(request, buzzer_id):
    """Update community siren buzzer"""
    try:
        try:
            buzzer = CommunitySirenBuzzer.objects.get(id=buzzer_id)
        except CommunitySirenBuzzer.DoesNotExist:
            raise NotFoundError("Community siren buzzer not found")
        
        serializer = CommunitySirenBuzzerUpdateSerializer(buzzer, data=request.data)
        
        if serializer.is_valid():
            buzzer = serializer.save()
            response_serializer = CommunitySirenBuzzerSerializer(buzzer)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Community siren buzzer updated successfully')
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
@require_auth
@require_community_siren_module_access(CommunitySirenBuzzer, 'buzzer_id')
@api_response
def delete_community_siren_buzzer(request, buzzer_id):
    """Delete community siren buzzer"""
    try:
        try:
            buzzer = CommunitySirenBuzzer.objects.get(id=buzzer_id)
        except CommunitySirenBuzzer.DoesNotExist:
            raise NotFoundError("Community siren buzzer not found")
        
        buzzer_title = buzzer.title
        buzzer.delete()
        
        return success_response(
            data={'id': buzzer_id},
            message=f"Community siren buzzer '{buzzer_title}' deleted successfully"
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
