"""
Alert Device Views
Handles alert device (buzzer/sos) management endpoints
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from device.models import Device, UserDevice, BuzzerStatus, SosStatus
from shared_utils.constants import DeviceType
from device.serializers.alert_device_serializers import AlertDeviceStatusSerializer


@api_view(['GET'])
def get_alert_devices(request):
    """
    Get user's assigned devices with type 'buzzer' or 'sos' and their latest status
    """
    try:
        user = request.user
        
        # Get user's assigned devices
        user_devices = UserDevice.objects.filter(user=user).select_related('device')
        
        # Filter devices by type (buzzer or sos) and get device objects
        devices_data = []
        
        for user_device in user_devices:
            device = user_device.device
            device_type = device.type or 'gps'
            
            # Only include buzzer and sos devices
            if device_type in [DeviceType.BUZZER, DeviceType.SOS]:
                # Get latest status from appropriate table
                latest_status = None
                status_table = None
                last_data_at = None
                
                if device_type == DeviceType.BUZZER:
                    # Get latest buzzer status
                    latest_status_record = BuzzerStatus.objects.filter(
                        imei=device.imei
                    ).order_by('-createdAt', '-updatedAt').first()
                    
                    if latest_status_record:
                        latest_status = {
                            'battery': latest_status_record.battery,
                            'signal': latest_status_record.signal,
                            'ignition': latest_status_record.ignition,
                            'charging': latest_status_record.charging,
                            'relay': latest_status_record.relay,
                        }
                        status_table = 'buzzer'
                        last_data_at = latest_status_record.updatedAt or latest_status_record.createdAt
                
                elif device_type == DeviceType.SOS:
                    # Get latest sos status
                    latest_status_record = SosStatus.objects.filter(
                        imei=device.imei
                    ).order_by('-createdAt', '-updatedAt').first()
                    
                    if latest_status_record:
                        latest_status = {
                            'battery': latest_status_record.battery,
                            'signal': latest_status_record.signal,
                            'ignition': latest_status_record.ignition,
                            'charging': latest_status_record.charging,
                            'relay': latest_status_record.relay,
                        }
                        status_table = 'sos'
                        last_data_at = latest_status_record.updatedAt or latest_status_record.createdAt
                
                # Check if device is inactive (last data > 1 hour)
                is_inactive = False
                if last_data_at:
                    time_since_last_data = timezone.now() - last_data_at
                    is_inactive = time_since_last_data > timedelta(hours=1)
                
                # Prepare device data
                device_data = {
                    'id': str(device.id),
                    'imei': device.imei,
                    'phone': device.phone,
                    'type': device_type,
                    'battery': latest_status['battery'] if latest_status else 0,
                    'signal': latest_status['signal'] if latest_status else 0,
                    'ignition': latest_status['ignition'] if latest_status else False,
                    'charging': latest_status['charging'] if latest_status else False,
                    'relay': latest_status['relay'] if latest_status else False,
                    'last_data_at': last_data_at,
                    'isInactive': is_inactive,
                    'status_table': status_table or device_type,
                }
                
                devices_data.append(device_data)
        
        serializer = AlertDeviceStatusSerializer(devices_data, many=True)
        
        return Response({
            'success': True,
            'message': f'Retrieved {len(devices_data)} alert devices',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error retrieving alert devices: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

