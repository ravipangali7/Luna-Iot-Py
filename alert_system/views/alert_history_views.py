"""
Alert History Views
Handles alert history management endpoints
"""
from rest_framework.decorators import api_view
from django.core.paginator import Paginator
from django.db.models import Q
from alert_system.models import AlertHistory
from alert_system.serializers import (
    AlertHistorySerializer,
    AlertHistoryCreateSerializer,
    AlertHistoryUpdateSerializer,
    AlertHistoryListSerializer,
    AlertHistoryStatusUpdateSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError


@api_view(['GET'])
@require_auth
@api_response
def get_all_alert_histories(request):
    """Get all alert histories with pagination and filtering"""
    try:
        search_query = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', '').strip()
        source_filter = request.GET.get('source', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        histories = AlertHistory.objects.select_related('alert_type', 'institute').all()
        
        if search_query:
            histories = histories.filter(
                Q(name__icontains=search_query) |
                Q(primary_phone__icontains=search_query) |
                Q(institute__name__icontains=search_query) |
                Q(alert_type__name__icontains=search_query)
            )
        
        if status_filter:
            histories = histories.filter(status=status_filter)
        
        if source_filter:
            histories = histories.filter(source=source_filter)
        
        histories = histories.order_by('-datetime')
        
        paginator = Paginator(histories, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = AlertHistoryListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert histories retrieved successfully'),
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
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_alert_history_by_id(request, history_id):
    """Get alert history by ID"""
    try:
        try:
            history = AlertHistory.objects.select_related('alert_type', 'institute').get(id=history_id)
        except AlertHistory.DoesNotExist:
            raise NotFoundError("Alert history not found")
        
        serializer = AlertHistorySerializer(history)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert history retrieved successfully')
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
def get_alert_histories_by_institute(request, institute_id):
    """Get alert histories by institute"""
    try:
        histories = AlertHistory.objects.select_related('alert_type').filter(institute_id=institute_id).order_by('-datetime')
        serializer = AlertHistoryListSerializer(histories, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert histories retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_alert_histories_by_radar(request, radar_id):
    """Get alert histories by radar (filtered by radar's geofences)"""
    try:
        # Get the radar and its associated geofences
        try:
            from alert_system.models import AlertRadar
            radar = AlertRadar.objects.prefetch_related('alert_geofences').get(id=radar_id)
        except AlertRadar.DoesNotExist:
            raise NotFoundError("Radar not found")
        
        # Get geofence IDs associated with this radar
        geofence_ids = radar.alert_geofences.values_list('id', flat=True)
        
        if not geofence_ids:
            # If radar has no geofences, return empty list
            return success_response(
                data=[],
                message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert histories retrieved successfully')
            )
        
        # Filter alert histories by geofences associated with this radar
        histories = AlertHistory.objects.select_related('alert_type', 'institute').filter(
            source='geofence',
            geofence_id__in=geofence_ids
        ).order_by('-datetime')
        
        serializer = AlertHistoryListSerializer(histories, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert histories retrieved successfully')
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
def get_alert_history_statistics(request):
    """Get alert history statistics"""
    try:
        from django.db.models import Count
        from shared_utils.constants import AlertStatus, AlertSource
        
        # Status counts
        status_counts = AlertHistory.objects.values('status').annotate(count=Count('id'))
        status_stats = {item['status']: item['count'] for item in status_counts}
        
        # Source counts
        source_counts = AlertHistory.objects.values('source').annotate(count=Count('id'))
        source_stats = {item['source']: item['count'] for item in source_counts}
        
        # Total counts
        total_alerts = AlertHistory.objects.count()
        pending_alerts = AlertHistory.objects.filter(status=AlertStatus.PENDING).count()
        approved_alerts = AlertHistory.objects.filter(status=AlertStatus.APPROVED).count()
        rejected_alerts = AlertHistory.objects.filter(status=AlertStatus.REJECTED).count()
        
        return success_response(
            data={
                'total_alerts': total_alerts,
                'pending_alerts': pending_alerts,
                'approved_alerts': approved_alerts,
                'rejected_alerts': rejected_alerts,
                'status_breakdown': status_stats,
                'source_breakdown': source_stats
            },
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert statistics retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_auth
@api_response
def create_alert_history(request):
    """Create new alert history"""
    try:
        serializer = AlertHistoryCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            history = serializer.save()
            response_serializer = AlertHistorySerializer(history)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Alert history created successfully'),
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
def update_alert_history(request, history_id):
    """Update alert history"""
    try:
        try:
            history = AlertHistory.objects.get(id=history_id)
        except AlertHistory.DoesNotExist:
            raise NotFoundError("Alert history not found")
        
        serializer = AlertHistoryUpdateSerializer(history, data=request.data)
        
        if serializer.is_valid():
            history = serializer.save()
            response_serializer = AlertHistorySerializer(history)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Alert history updated successfully')
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


@api_view(['PUT'])
@require_auth  # Changed from require_super_admin to allow any authenticated user
@api_response
def update_alert_history_status(request, history_id):
    """Update alert history status only"""
    try:
        try:
            history = AlertHistory.objects.get(id=history_id)
        except AlertHistory.DoesNotExist:
            raise NotFoundError("Alert history not found")
        
        serializer = AlertHistoryStatusUpdateSerializer(history, data=request.data)
        
        if serializer.is_valid():
            history = serializer.save()
            response_serializer = AlertHistorySerializer(history)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Alert history status updated successfully')
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


@api_view(['PUT'])
@require_auth  # Changed from require_super_admin to allow any authenticated user
@api_response
def update_alert_history_remarks(request, history_id):
    """Update alert history remarks only"""
    try:
        try:
            history = AlertHistory.objects.get(id=history_id)
        except AlertHistory.DoesNotExist:
            raise NotFoundError("Alert history not found")
        
        # Validate remarks field
        remarks = request.data.get('remarks')
        if remarks is None:
            return error_response(
                message='Remarks field is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Update remarks
        history.remarks = remarks
        history.save()
        
        response_serializer = AlertHistorySerializer(history)
        
        return success_response(
            data=response_serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Alert history remarks updated successfully')
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
def delete_alert_history(request, history_id):
    """Delete alert history"""
    try:
        try:
            history = AlertHistory.objects.get(id=history_id)
        except AlertHistory.DoesNotExist:
            raise NotFoundError("Alert history not found")
        
        history_name = history.name
        history.delete()
        
        return success_response(
            data={'id': history_id},
            message=f"Alert history '{history_name}' deleted successfully"
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
