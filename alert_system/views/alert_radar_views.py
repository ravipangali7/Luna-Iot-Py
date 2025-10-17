"""
Alert Radar Views
Handles alert radar management endpoints
"""
from rest_framework.decorators import api_view
from django.core.paginator import Paginator
from django.db.models import Q
from alert_system.models import AlertRadar
from alert_system.serializers import (
    AlertRadarSerializer,
    AlertRadarCreateSerializer,
    AlertRadarUpdateSerializer,
    AlertRadarListSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError


@api_view(['GET'])
@require_auth
@api_response
def get_all_alert_radars(request):
    """Get all alert radars"""
    try:
        radars = AlertRadar.objects.prefetch_related('alert_geofences').select_related('institute').all().order_by('-created_at')
        serializer = AlertRadarListSerializer(radars, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert radars retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_alert_radar_by_id(request, radar_id):
    """Get alert radar by ID"""
    try:
        try:
            radar = AlertRadar.objects.prefetch_related('alert_geofences').select_related('institute').get(id=radar_id)
        except AlertRadar.DoesNotExist:
            raise NotFoundError("Alert radar not found")
        
        serializer = AlertRadarSerializer(radar)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert radar retrieved successfully')
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
def get_alert_radars_by_institute(request, institute_id):
    """Get alert radars by institute"""
    try:
        radars = AlertRadar.objects.prefetch_related('alert_geofences').filter(institute_id=institute_id).order_by('-created_at')
        serializer = AlertRadarListSerializer(radars, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert radars retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )


@api_view(['POST'])
@require_super_admin
@api_response
def create_alert_radar(request):
    """Create new alert radar"""
    try:
        serializer = AlertRadarCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            radar = serializer.save()
            response_serializer = AlertRadarSerializer(radar)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Alert radar created successfully'),
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
def update_alert_radar(request, radar_id):
    """Update alert radar"""
    try:
        try:
            radar = AlertRadar.objects.get(id=radar_id)
        except AlertRadar.DoesNotExist:
            raise NotFoundError("Alert radar not found")
        
        serializer = AlertRadarUpdateSerializer(radar, data=request.data)
        
        if serializer.is_valid():
            radar = serializer.save()
            response_serializer = AlertRadarSerializer(radar)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Alert radar updated successfully')
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
def delete_alert_radar(request, radar_id):
    """Delete alert radar"""
    try:
        try:
            radar = AlertRadar.objects.get(id=radar_id)
        except AlertRadar.DoesNotExist:
            raise NotFoundError("Alert radar not found")
        
        radar_title = radar.title
        radar.delete()
        
        return success_response(
            data={'id': radar_id},
            message=f"Alert radar '{radar_title}' deleted successfully"
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
