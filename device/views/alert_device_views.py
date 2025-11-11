"""
Alert Device Views
Handles alert device (buzzer/sos) management endpoints
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from device.models import Device, BuzzerStatus, SosStatus
from core.models import InstituteModule
from alert_system.models import AlertBuzzer, AlertSwitch
from shared_utils.constants import DeviceType
from device.serializers.alert_device_serializers import AlertDeviceStatusSerializer


@api_view(['GET'])
def get_alert_devices(request):
    """
    Get devices with type 'buzzer' or 'sos' from institutes where user has alert-system module access.
    Super Admin users see all devices, others see only devices from their assigned institutes.
    """
    try:
        user = request.user
        
        # Check if user is Super Admin
        is_super_admin = user.groups.filter(name='Super Admin').exists()
        
        if is_super_admin:
            # Super Admin: Get all alert buzzers and switches
            alert_buzzers = AlertBuzzer.objects.select_related('device', 'institute').all()
            alert_switches = AlertSwitch.objects.select_related('device', 'institute').all()
        else:
            # Non-admin: Get user's institute modules where module is alert-system
            institute_modules = InstituteModule.objects.filter(
                users=user,
                module__slug='alert-system'
            ).select_related('institute', 'module')
            
            # Extract institute IDs
            institute_ids = [im.institute_id for im in institute_modules]
            
            if not institute_ids:
                return Response({
                    'success': True,
                    'message': 'No alert system modules assigned',
                    'data': []
                }, status=status.HTTP_200_OK)
            
            # Get all alert buzzers and switches from user's institutes
            alert_buzzers = AlertBuzzer.objects.filter(
                institute_id__in=institute_ids
            ).select_related('device', 'institute')
            
            alert_switches = AlertSwitch.objects.filter(
                institute_id__in=institute_ids
            ).select_related('device', 'institute')
        
        # Collect unique devices from alert entities
        devices_data = []
        processed_devices = set()  # Track processed device IDs to avoid duplicates
        
        # Process alert buzzers (buzzer devices)
        for alert_buzzer in alert_buzzers:
            device = alert_buzzer.device
            device_id = str(device.id)
            
            if device_id in processed_devices:
                continue
            
            processed_devices.add(device_id)
            
            # Get latest buzzer status
            latest_status_record = BuzzerStatus.objects.filter(
                imei=device.imei
            ).order_by('-createdAt', '-updatedAt').first()
            
            latest_status = None
            last_data_at = None
            
            if latest_status_record:
                latest_status = {
                    'battery': latest_status_record.battery,
                    'signal': latest_status_record.signal,
                    'ignition': latest_status_record.ignition,
                    'charging': latest_status_record.charging,
                    'relay': latest_status_record.relay,
                }
                last_data_at = latest_status_record.updatedAt or latest_status_record.createdAt
            
            # Check if device is inactive (last data > 1 hour)
            is_inactive = False
            if last_data_at:
                time_since_last_data = timezone.now() - last_data_at
                is_inactive = time_since_last_data > timedelta(hours=1)
            
            # Prepare device data
            device_data = {
                'id': device_id,
                'imei': device.imei,
                'phone': device.phone,
                'type': DeviceType.BUZZER,
                'title': alert_buzzer.title,
                'battery': latest_status['battery'] if latest_status else 0,
                'signal': latest_status['signal'] if latest_status else 0,
                'ignition': latest_status['ignition'] if latest_status else False,
                'charging': latest_status['charging'] if latest_status else False,
                'relay': latest_status['relay'] if latest_status else False,
                'last_data_at': last_data_at,
                'isInactive': is_inactive,
                'status_table': 'buzzer',
                'institute': {
                    'id': alert_buzzer.institute.id,
                    'name': alert_buzzer.institute.name,
                    'logo': request.build_absolute_uri(alert_buzzer.institute.logo.url) if alert_buzzer.institute.logo else None,
                }
            }
            
            devices_data.append(device_data)
            print(f"✅ Buzzer Device {device_id}: Institute = {alert_buzzer.institute.name}, Logo = {alert_buzzer.institute.logo.url if alert_buzzer.institute.logo else 'NULL'}")
        
        # Process alert switches (sos devices)
        for alert_switch in alert_switches:
            device = alert_switch.device
            device_id = str(device.id)
            
            if device_id in processed_devices:
                continue
            
            processed_devices.add(device_id)
            
            # Get latest sos status
            latest_status_record = SosStatus.objects.filter(
                imei=device.imei
            ).order_by('-createdAt', '-updatedAt').first()
            
            latest_status = None
            last_data_at = None
            
            if latest_status_record:
                latest_status = {
                    'battery': latest_status_record.battery,
                    'signal': latest_status_record.signal,
                    'ignition': latest_status_record.ignition,
                    'charging': latest_status_record.charging,
                    'relay': latest_status_record.relay,
                }
                last_data_at = latest_status_record.updatedAt or latest_status_record.createdAt
            
            # Check if device is inactive (last data > 1 hour)
            is_inactive = False
            if last_data_at:
                time_since_last_data = timezone.now() - last_data_at
                is_inactive = time_since_last_data > timedelta(hours=1)
            
            # Prepare device data
            device_data = {
                'id': device_id,
                'imei': device.imei,
                'phone': device.phone,
                'type': DeviceType.SOS,
                'title': alert_switch.title,
                'battery': latest_status['battery'] if latest_status else 0,
                'signal': latest_status['signal'] if latest_status else 0,
                'ignition': latest_status['ignition'] if latest_status else False,
                'charging': latest_status['charging'] if latest_status else False,
                'relay': latest_status['relay'] if latest_status else False,
                'last_data_at': last_data_at,
                'isInactive': is_inactive,
                'status_table': 'sos',
                'institute': {
                    'id': alert_switch.institute.id,
                    'name': alert_switch.institute.name,
                    'logo': request.build_absolute_uri(alert_switch.institute.logo.url) if alert_switch.institute.logo else None,
                }
            }
            
            devices_data.append(device_data)
            print(f"✅ SOS Device {device_id}: Institute = {alert_switch.institute.name}, Logo = {alert_switch.institute.logo.url if alert_switch.institute.logo else 'NULL'}")
        
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

