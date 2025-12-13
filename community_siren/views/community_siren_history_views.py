"""
Community Siren History Views
Handles community siren history management endpoints
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.core.paginator import Paginator
from django.db.models import Q
from community_siren.models import CommunitySirenHistory, CommunitySirenBuzzer, CommunitySirenSwitch
from community_siren.serializers import (
    CommunitySirenHistorySerializer,
    CommunitySirenHistoryCreateSerializer,
    CommunitySirenHistoryUpdateSerializer,
    CommunitySirenHistoryListSerializer,
    CommunitySirenHistoryStatusUpdateSerializer
)
from community_siren.tasks import schedule_relay_off_command
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth
from api_common.exceptions.api_exceptions import NotFoundError
from core.models import Module, InstituteModule
from api_common.utils.tcp_service import tcp_service
from functools import wraps
import logging

logger = logging.getLogger(__name__)


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
                record_id = kwargs.get(id_param_name) or kwargs.get('history_id')
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
def get_all_community_siren_histories(request):
    """Get all community siren histories with pagination and filtering"""
    try:
        search_query = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', '').strip()
        source_filter = request.GET.get('source', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        histories = CommunitySirenHistory.objects.select_related('institute').all()
        
        if search_query:
            histories = histories.filter(
                Q(name__icontains=search_query) |
                Q(primary_phone__icontains=search_query) |
                Q(institute__name__icontains=search_query)
            )
        
        if status_filter:
            histories = histories.filter(status=status_filter)
        
        if source_filter:
            histories = histories.filter(source=source_filter)
        
        histories = histories.order_by('-datetime')
        
        paginator = Paginator(histories, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = CommunitySirenHistoryListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Community siren histories retrieved successfully'),
            data={
                'histories': serializer.data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'page_size': page_size,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        )
    except Exception as e:
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))


@api_view(['GET'])
@require_auth
@api_response
def get_community_siren_history_by_id(request, history_id):
    """Get community siren history by ID"""
    try:
        try:
            history = CommunitySirenHistory.objects.select_related('institute').get(id=history_id)
        except CommunitySirenHistory.DoesNotExist:
            raise NotFoundError("Community siren history not found")
        serializer = CommunitySirenHistorySerializer(history)
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Community siren history retrieved successfully')
        )
    except NotFoundError as e:
        return error_response(message=str(e), status_code=HTTP_STATUS['NOT_FOUND'])
    except Exception as e:
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))


@api_view(['GET'])
@require_auth
@api_response
def get_community_siren_histories_by_institute(request, institute_id):
    """Get community siren histories by institute"""
    try:
        search_query = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', '').strip()
        source_filter = request.GET.get('source', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        histories = CommunitySirenHistory.objects.filter(institute_id=institute_id)
        
        if search_query:
            histories = histories.filter(
                Q(name__icontains=search_query) |
                Q(primary_phone__icontains=search_query)
            )
        
        if status_filter:
            histories = histories.filter(status=status_filter)
        
        if source_filter:
            histories = histories.filter(source=source_filter)
        
        histories = histories.order_by('-datetime')
        
        paginator = Paginator(histories, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = CommunitySirenHistoryListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Community siren histories retrieved successfully'),
            data={
                'histories': serializer.data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'page_size': page_size,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        )
    except Exception as e:
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))


@api_view(['POST'])
@permission_classes([AllowAny])
@api_response
def create_community_siren_history(request):
    """Create new community siren history and control buzzer/switch relay with timing"""
    try:
        serializer = CommunitySirenHistoryCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Get institute and source from validated data
            institute = serializer.validated_data.get('institute')
            source = serializer.validated_data.get('source', 'app')
            
            # Set member to current user if not provided and user is authenticated
            if ('member' not in serializer.validated_data or serializer.validated_data.get('member') is None) and request.user.is_authenticated:
                serializer.validated_data['member'] = request.user
            
            # Create history first
            history = serializer.save()
            
            # Handle relay commands after history is created (so we have history.id for logging)
            if institute:
                # Handle buzzer relay commands (for both 'app' and 'switch' sources)
                buzzer = None
                try:
                    buzzer = CommunitySirenBuzzer.objects.filter(institute=institute).first()
                except Exception as e:
                    logger.warning(f"Could not find buzzer for institute {institute.id}: {str(e)}")
                
                # Turn relay ON and schedule OFF for buzzer
                if buzzer and buzzer.device and buzzer.device.imei:
                    try:
                        buzzer_imei = buzzer.device.imei
                        logger.info(f"Turning relay ON for buzzer device IMEI: {buzzer_imei}")
                        relay_on_result = tcp_service.send_relay_on_command(buzzer_imei)
                        
                        if relay_on_result.get('success'):
                            logger.info(f"Relay ON sent to buzzer {buzzer.title} (IMEI: {buzzer_imei})")
                            
                            # Schedule relay OFF for buzzer after delay
                            schedule_relay_off_command(
                                buzzer_imei,
                                buzzer.delay,
                                history.id,
                                buzzer_id=buzzer.id
                            )
                        else:
                            logger.warning(f"Failed to send relay ON to buzzer {buzzer.title} (IMEI: {buzzer_imei}): {relay_on_result.get('message', 'Unknown error')}")
                    except Exception as e:
                        logger.error(f"Error handling buzzer relay commands: {str(e)}")
                        # Continue even if relay control fails
                
                # Handle switch device relay commands if source is 'switch'
                if source == 'switch':
                    switch = None
                    try:
                        # Try to find switch by institute and location proximity
                        # For now, get first switch for the institute
                        switch = CommunitySirenSwitch.objects.filter(institute=institute).first()
                    except Exception as e:
                        logger.warning(f"Could not find switch for institute {institute.id}: {str(e)}")
                    
                    if switch and switch.device and switch.device.imei:
                        try:
                            switch_imei = switch.device.imei
                            logger.info(f"Turning relay ON for switch device IMEI: {switch_imei}")
                            switch_relay_on_result = tcp_service.send_relay_on_command(switch_imei)
                            
                            if switch_relay_on_result.get('success'):
                                logger.info(f"Relay ON sent to switch {switch.title} (IMEI: {switch_imei})")
                                
                                # Schedule relay OFF for switch after trigger delay
                                schedule_relay_off_command(
                                    switch_imei,
                                    switch.trigger,
                                    history.id,
                                    switch_id=switch.id
                                )
                            else:
                                logger.warning(f"Failed to send relay ON to switch {switch.title} (IMEI: {switch_imei}): {switch_relay_on_result.get('message', 'Unknown error')}")
                        except Exception as e:
                            logger.error(f"Error handling switch relay commands: {str(e)}")
                            # Continue even if relay control fails
            
            response_serializer = CommunitySirenHistorySerializer(history)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Community siren history created successfully'),
                status_code=HTTP_STATUS['CREATED']
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except Exception as e:
        logger.exception(f"Error creating community siren history: {str(e)}")
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))


@api_view(['PUT'])
@require_auth
@require_community_siren_module_access(CommunitySirenHistory, 'history_id')
@api_response
def update_community_siren_history(request, history_id):
    """Update community siren history"""
    try:
        try:
            history = CommunitySirenHistory.objects.get(id=history_id)
        except CommunitySirenHistory.DoesNotExist:
            raise NotFoundError("Community siren history not found")
        serializer = CommunitySirenHistoryUpdateSerializer(history, data=request.data)
        if serializer.is_valid():
            history = serializer.save()
            response_serializer = CommunitySirenHistorySerializer(history)
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Community siren history updated successfully')
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


@api_view(['PATCH'])
@require_auth
@require_community_siren_module_access(CommunitySirenHistory, 'history_id')
@api_response
def update_community_siren_history_status(request, history_id):
    """Update community siren history status only"""
    try:
        try:
            history = CommunitySirenHistory.objects.get(id=history_id)
        except CommunitySirenHistory.DoesNotExist:
            raise NotFoundError("Community siren history not found")
        serializer = CommunitySirenHistoryStatusUpdateSerializer(history, data=request.data)
        if serializer.is_valid():
            history = serializer.save()
            response_serializer = CommunitySirenHistorySerializer(history)
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Community siren history status updated successfully')
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
@require_community_siren_module_access(CommunitySirenHistory, 'history_id')
@api_response
def delete_community_siren_history(request, history_id):
    """Delete community siren history"""
    try:
        try:
            history = CommunitySirenHistory.objects.get(id=history_id)
        except CommunitySirenHistory.DoesNotExist:
            raise NotFoundError("Community siren history not found")
        history.delete()
        return success_response(
            data={'id': history_id},
            message="Community siren history deleted successfully"
        )
    except NotFoundError as e:
        return error_response(message=str(e), status_code=HTTP_STATUS['NOT_FOUND'])
    except Exception as e:
        return error_response(message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'), data=str(e))
