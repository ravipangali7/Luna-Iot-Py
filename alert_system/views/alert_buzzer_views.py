"""
Alert Buzzer Views
Handles alert buzzer management endpoints
"""
from rest_framework.decorators import api_view
from alert_system.models import AlertBuzzer
from alert_system.serializers import (
    AlertBuzzerSerializer,
    AlertBuzzerCreateSerializer,
    AlertBuzzerUpdateSerializer,
    AlertBuzzerListSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError


@api_view(['GET'])
@require_auth
@api_response
def get_all_alert_buzzers(request):
    """Get all alert buzzers"""
    try:
        buzzers = AlertBuzzer.objects.prefetch_related('alert_geofences').select_related('institute', 'device').all().order_by('-created_at')
        serializer = AlertBuzzerListSerializer(buzzers, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert buzzers retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_alert_buzzer_by_id(request, buzzer_id):
    """Get alert buzzer by ID"""
    try:
        try:
            buzzer = AlertBuzzer.objects.prefetch_related('alert_geofences').select_related('institute', 'device').get(id=buzzer_id)
        except AlertBuzzer.DoesNotExist:
            raise NotFoundError("Alert buzzer not found")
        
        serializer = AlertBuzzerSerializer(buzzer)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert buzzer retrieved successfully')
        )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_alert_buzzers_by_institute(request, institute_id):
    """Get alert buzzers by institute"""
    try:
        buzzers = AlertBuzzer.objects.prefetch_related('alert_geofences').select_related('device').filter(institute_id=institute_id).order_by('-created_at')
        serializer = AlertBuzzerListSerializer(buzzers, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert buzzers retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )


@api_view(['POST'])
@require_super_admin
@api_response
def create_alert_buzzer(request):
    """Create new alert buzzer"""
    try:
        serializer = AlertBuzzerCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            buzzer = serializer.save()
            response_serializer = AlertBuzzerSerializer(buzzer)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Alert buzzer created successfully'),
                status_code=HTTP_STATUS['CREATED']
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                details=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )


@api_view(['PUT'])
@require_super_admin
@api_response
def update_alert_buzzer(request, buzzer_id):
    """Update alert buzzer"""
    try:
        try:
            buzzer = AlertBuzzer.objects.get(id=buzzer_id)
        except AlertBuzzer.DoesNotExist:
            raise NotFoundError("Alert buzzer not found")
        
        serializer = AlertBuzzerUpdateSerializer(buzzer, data=request.data)
        
        if serializer.is_valid():
            buzzer = serializer.save()
            response_serializer = AlertBuzzerSerializer(buzzer)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Alert buzzer updated successfully')
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                details=serializer.errors,
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
            details=str(e)
        )


@api_view(['DELETE'])
@require_super_admin
@api_response
def delete_alert_buzzer(request, buzzer_id):
    """Delete alert buzzer"""
    try:
        try:
            buzzer = AlertBuzzer.objects.get(id=buzzer_id)
        except AlertBuzzer.DoesNotExist:
            raise NotFoundError("Alert buzzer not found")
        
        buzzer_title = buzzer.title
        buzzer.delete()
        
        return success_response(
            data={'id': buzzer_id},
            message=f"Alert buzzer '{buzzer_title}' deleted successfully"
        )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )
