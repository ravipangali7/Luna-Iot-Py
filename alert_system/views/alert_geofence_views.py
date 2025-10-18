"""
Alert Geofence Views
Handles alert geofence management endpoints
"""
from rest_framework.decorators import api_view
from django.core.paginator import Paginator
from django.db.models import Q
from alert_system.models import AlertGeofence
from alert_system.serializers import (
    AlertGeofenceSerializer,
    AlertGeofenceCreateSerializer,
    AlertGeofenceUpdateSerializer,
    AlertGeofenceListSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError


@api_view(['GET'])
@require_auth
@api_response
def get_all_alert_geofences(request):
    """Get all alert geofences with pagination"""
    try:
        search_query = request.GET.get('search', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        geofences = AlertGeofence.objects.prefetch_related('alert_types').select_related('institute').all()
        
        if search_query:
            geofences = geofences.filter(
                Q(title__icontains=search_query) |
                Q(institute__name__icontains=search_query)
            )
        
        geofences = geofences.order_by('-created_at')
        
        paginator = Paginator(geofences, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = AlertGeofenceListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert geofences retrieved successfully'),
            data={
                'geofences': serializer.data,
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
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_alert_geofence_by_id(request, geofence_id):
    """Get alert geofence by ID"""
    try:
        try:
            geofence = AlertGeofence.objects.prefetch_related('alert_types').select_related('institute').get(id=geofence_id)
        except AlertGeofence.DoesNotExist:
            raise NotFoundError("Alert geofence not found")
        
        serializer = AlertGeofenceSerializer(geofence)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert geofence retrieved successfully')
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
def get_alert_geofences_by_institute(request, institute_id):
    """Get alert geofences by institute"""
    try:
        geofences = AlertGeofence.objects.prefetch_related('alert_types').filter(institute_id=institute_id).order_by('-created_at')
        serializer = AlertGeofenceListSerializer(geofences, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert geofences retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_super_admin
@api_response
def create_alert_geofence(request):
    """Create new alert geofence"""
    try:
        serializer = AlertGeofenceCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            geofence = serializer.save()
            response_serializer = AlertGeofenceSerializer(geofence)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Alert geofence created successfully'),
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
def update_alert_geofence(request, geofence_id):
    """Update alert geofence"""
    try:
        try:
            geofence = AlertGeofence.objects.get(id=geofence_id)
        except AlertGeofence.DoesNotExist:
            raise NotFoundError("Alert geofence not found")
        
        serializer = AlertGeofenceUpdateSerializer(geofence, data=request.data)
        
        if serializer.is_valid():
            geofence = serializer.save()
            response_serializer = AlertGeofenceSerializer(geofence)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Alert geofence updated successfully')
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
def delete_alert_geofence(request, geofence_id):
    """Delete alert geofence"""
    try:
        try:
            geofence = AlertGeofence.objects.get(id=geofence_id)
        except AlertGeofence.DoesNotExist:
            raise NotFoundError("Alert geofence not found")
        
        geofence_title = geofence.title
        geofence.delete()
        
        return success_response(
            data={'id': geofence_id},
            message=f"Alert geofence '{geofence_title}' deleted successfully"
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
def get_sos_alert_geofences(request):
    """Get all alert geofences for SOS (no pagination, includes institute coordinates)"""
    try:
        geofences = AlertGeofence.objects.prefetch_related('alert_types').select_related('institute').all()
        serializer = AlertGeofenceSerializer(geofences, many=True)
        
        return success_response(
            data=serializer.data,
            message='Alert geofences for SOS retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message='Failed to retrieve SOS alert geofences',
            data=str(e)
        )