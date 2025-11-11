"""
Luna Tag Data Views
Handles LunaTagData read-only endpoints
"""
from datetime import datetime
from rest_framework.decorators import api_view

from device.models import LunaTagData, LunaTag
from device.serializers import LunaTagDataSerializer
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth


@api_view(['GET'])
@require_auth
@api_response
def get_luna_tag_data(request, publicKey):
    """
    Get latest LunaTagData for a specific publicKey
    """
    try:
        try:
            luna_tag = LunaTag.objects.get(publicKey=publicKey)
        except LunaTag.DoesNotExist:
            return error_response(
                message='Luna Tag not found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Get latest data
        latest_data = LunaTagData.objects.filter(publicKey=luna_tag).order_by('-created_at').first()
        
        if not latest_data:
            return error_response(
                message='No data found for this Luna Tag',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        serializer = LunaTagDataSerializer(latest_data)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Luna Tag data retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_luna_tag_data_by_date_range(request, publicKey):
    """
    Get LunaTagData by date range for a specific publicKey
    Returns data ordered by created_at in ascending order (for playback)
    """
    try:
        try:
            luna_tag = LunaTag.objects.get(publicKey=publicKey)
        except LunaTag.DoesNotExist:
            return error_response(
                message='Luna Tag not found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        start_date = request.GET.get('startDate')
        end_date = request.GET.get('endDate')
        
        if not start_date or not end_date:
            return error_response(
                message='Start date and end date are required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Parse dates (format: YYYY-MM-DD)
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            # Set end date to end of day
            end = end.replace(hour=23, minute=59, second=59)
        except ValueError as e:
            return error_response(
                message=f'Invalid date format: {str(e)}',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Filter by publicKey and date range, order by created_at ascending (for playback timeline)
        luna_tag_data = LunaTagData.objects.filter(
            publicKey=luna_tag,
            created_at__range=[start, end]
        ).order_by('created_at')  # Ascending order for playback
        
        # Serialize data
        serializer = LunaTagDataSerializer(luna_tag_data, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Luna Tag data retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )

