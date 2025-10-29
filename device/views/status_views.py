"""
Status Views
Handles status tracking endpoints
Matches Node.js status_controller.js functionality exactly
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

from device.models.status import Status
from device.models.buzzer_status import BuzzerStatus
from device.models.sos_status import SosStatus
from device.models.device import Device
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.exceptions.api_exceptions import NotFoundError, ValidationError


@api_view(['POST'])
@api_response
def create_status(request):
    """
    Create new status record
    For Node.js GT06 handler to send status data
    """
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['imei', 'battery', 'signal', 'ignition', 'charging', 'relay', 'created_at']
        for field in required_fields:
            if field not in data:
                return error_response(
                    message=f'Missing required field: {field}',
                    status_code=HTTP_STATUS['BAD_REQUEST']
                )
        
        # Check if device exists
        try:
            device = Device.objects.get(imei=data['imei'])
        except Device.DoesNotExist:
            return error_response(
                message='Device not found with IMEI: ' + data['imei'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Get device type for routing
        device_type = (device.type or 'gps').lower()
        
        # Check if any vehicle with this IMEI is active (only for GPS devices)
        # Buzzer and SOS devices may not have associated vehicles
        if device_type == 'gps':
            from fleet.models import Vehicle
            active_vehicles = Vehicle.objects.filter(imei=data['imei'], is_active=True)
            if not active_vehicles.exists():
                return error_response(
                    message='No active vehicle found with IMEI: ' + data['imei'],
                    status_code=HTTP_STATUS['BAD_REQUEST']
                )
        
        # Route to appropriate status table based on device type
        if device_type == 'sos':
            status_obj = SosStatus.objects.create(
                device=device,
                imei=data['imei'],
                battery=data['battery'],
                signal=data['signal'],
                ignition=data['ignition'],
                charging=data['charging'],
                relay=data['relay'],
                createdAt=data['created_at']
            )
        elif device_type == 'buzzer':
            status_obj = BuzzerStatus.objects.create(
                device=device,
                imei=data['imei'],
                battery=data['battery'],
                signal=data['signal'],
                ignition=data['ignition'],
                charging=data['charging'],
                relay=data['relay'],
                createdAt=data['created_at']
            )
        else:
            # Default to GPS status
            status_obj = Status.objects.create(
                device=device,
                imei=data['imei'],
                battery=data['battery'],
                signal=data['signal'],
                ignition=data['ignition'],
                charging=data['charging'],
                relay=data['relay'],
                createdAt=data['created_at']
            )
        
        status_data = {
            'id': status_obj.id,
            'imei': status_obj.imei,
            'battery': status_obj.battery,
            'signal': status_obj.signal,
            'ignition': status_obj.ignition,
            'charging': status_obj.charging,
            'relay': status_obj.relay,
            'createdAt': status_obj.createdAt.isoformat()
        }
        
        return success_response(
            data=status_data,
            message='Status created successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@api_response
def get_status_by_imei(request, imei):
    """
    Get status history by IMEI
    Matches Node.js StatusController.getStatusByImei
    """
    try:
        statuses = Status.objects.filter(imei=imei).order_by('-createdAt')
        statuses_data = []
        
        for status_obj in statuses:
            statuses_data.append({
                'id': status_obj.id,
                'imei': status_obj.imei,
                'battery': status_obj.battery,
                'signal': status_obj.signal,
                'ignition': status_obj.ignition,
                'charging': status_obj.charging,
                'relay': status_obj.relay,
                'createdAt': status_obj.createdAt.isoformat()
            })
        
        return success_response(
            data=statuses_data,
            message='Status history retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@api_response
def get_latest_status(request, imei):
    """
    Get latest status by IMEI
    Matches Node.js StatusController.getLatestStatus
    """
    try:
        try:
            status_obj = Status.objects.filter(imei=imei).order_by('-createdAt').first()
        except Status.DoesNotExist:
            return error_response(
                message='No status data found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        if not status_obj:
            return error_response(
                message='No status data found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        status_data = {
            'id': status_obj.id,
            'imei': status_obj.imei,
            'battery': status_obj.battery,
            'signal': status_obj.signal,
            'ignition': status_obj.ignition,
            'charging': status_obj.charging,
            'relay': status_obj.relay,
            'createdAt': status_obj.createdAt.isoformat()
        }
        
        return success_response(
            data=status_data,
            message='Latest status retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@api_response
def get_status_by_date_range(request, imei):
    """
    Get status by date range
    Matches Node.js StatusController.getStatusByDateRange
    """
    try:
        start_date = request.GET.get('startDate')
        end_date = request.GET.get('endDate')
        
        if not start_date or not end_date:
            return error_response(
                message='Start date and end date are required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        statuses = Status.objects.filter(
            imei=imei,
            createdAt__range=[start, end]
        ).order_by('-createdAt')
        
        statuses_data = []
        for status_obj in statuses:
            statuses_data.append({
                'id': status_obj.id,
                'imei': status_obj.imei,
                'battery': status_obj.battery,
                'signal': status_obj.signal,
                'ignition': status_obj.ignition,
                'charging': status_obj.charging,
                'relay': status_obj.relay,
                'createdAt': status_obj.createdAt.isoformat()
            })
        
        return success_response(
            data=statuses_data,
            message='Status data retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )
