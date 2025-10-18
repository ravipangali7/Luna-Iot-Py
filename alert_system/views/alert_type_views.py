"""
Alert Type Views
Handles alert type management endpoints
"""
from rest_framework.decorators import api_view
from alert_system.models import AlertType
from alert_system.serializers import (
    AlertTypeSerializer,
    AlertTypeCreateSerializer,
    AlertTypeUpdateSerializer,
    AlertTypeListSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError


@api_view(['GET'])
@require_auth
@api_response
def get_all_alert_types(request):
    """Get all alert types"""
    try:
        alert_types = AlertType.objects.all().order_by('name')
        serializer = AlertTypeListSerializer(alert_types, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert types retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_alert_type_by_id(request, alert_type_id):
    """Get alert type by ID"""
    try:
        try:
            alert_type = AlertType.objects.get(id=alert_type_id)
        except AlertType.DoesNotExist:
            raise NotFoundError("Alert type not found")
        
        serializer = AlertTypeSerializer(alert_type)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert type retrieved successfully')
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


@api_view(['POST'])
@require_super_admin
@api_response
def create_alert_type(request):
    """Create new alert type"""
    try:
        serializer = AlertTypeCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            alert_type = serializer.save()
            response_serializer = AlertTypeSerializer(alert_type)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Alert type created successfully'),
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
@require_super_admin
@api_response
def update_alert_type(request, alert_type_id):
    """Update alert type"""
    try:
        try:
            alert_type = AlertType.objects.get(id=alert_type_id)
        except AlertType.DoesNotExist:
            raise NotFoundError("Alert type not found")
        
        serializer = AlertTypeUpdateSerializer(alert_type, data=request.data)
        
        if serializer.is_valid():
            alert_type = serializer.save()
            response_serializer = AlertTypeSerializer(alert_type)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Alert type updated successfully')
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
@require_super_admin
@api_response
def delete_alert_type(request, alert_type_id):
    """Delete alert type"""
    try:
        try:
            alert_type = AlertType.objects.get(id=alert_type_id)
        except AlertType.DoesNotExist:
            raise NotFoundError("Alert type not found")
        
        alert_type_name = alert_type.name
        alert_type.delete()
        
        return success_response(
            data={'id': alert_type_id},
            message=f"Alert type '{alert_type_name}' deleted successfully"
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
