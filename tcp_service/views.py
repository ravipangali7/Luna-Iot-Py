"""
TCP Service Views

API endpoints for dashcam device management and SMS commands.
"""
import os
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from device.models import Device
from .protocol.constants import SMS_COMMAND_SERVER_POINT, SMS_COMMAND_RESET

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dashcam_command(request):
    """
    Send SMS command to dashcam device.
    
    POST /api/tcp-service/dashcam/command/
    
    Body:
        {
            "imei": "123456789012345",
            "action": "server_point" | "reset"
        }
    
    Actions:
        - server_point: Configure device to connect to our server
        - reset: Factory reset the device
    """
    imei = request.data.get('imei')
    action = request.data.get('action')
    
    if not imei:
        return Response(
            {'error': 'IMEI is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if action not in ['server_point', 'reset']:
        return Response(
            {'error': 'Invalid action. Must be "server_point" or "reset"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get device
    try:
        device = Device.objects.get(imei=imei)
    except Device.DoesNotExist:
        return Response(
            {'error': 'Device not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check device type
    if device.type != 'dashcam':
        return Response(
            {'error': 'Device is not a dashcam'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Build SMS message
    if action == 'server_point':
        server_ip = os.environ.get('PUBLIC_IP', '82.180.145.220')
        server_port = os.environ.get('JT808_PORT', '6665')
        message = SMS_COMMAND_SERVER_POINT.format(ip=server_ip, port=server_port)
    else:  # reset
        message = SMS_COMMAND_RESET
    
    # Send SMS
    phone_number = device.phone
    success = send_sms(phone_number, message)
    
    if success:
        logger.info(f"[DashcamCommand] Sent {action} command to {imei} ({phone_number})")
        return Response({
            'success': True,
            'message': f'{action} command sent successfully',
            'imei': imei,
            'phone': phone_number,
            'sms_message': message
        })
    else:
        logger.error(f"[DashcamCommand] Failed to send {action} command to {imei}")
        return Response(
            {'error': 'Failed to send SMS'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def send_sms(phone_number: str, message: str) -> bool:
    """
    Send SMS to a phone number.
    
    This is a placeholder - implement actual SMS sending using your SMS gateway.
    Options include:
    - Twilio
    - Sparrow SMS (Nepal)
    - Aakash SMS
    - Custom HTTP API
    
    Args:
        phone_number: Recipient phone number
        message: SMS message content
    
    Returns:
        True if sent successfully
    """
    # For now, just log the message
    logger.info(f"[SMS] Sending to {phone_number}: {message}")
    
    # TODO: Implement actual SMS sending
    # Example with Sparrow SMS:
    # try:
    #     import requests
    #     response = requests.post(
    #         'http://api.sparrowsms.com/v2/sms/',
    #         data={
    #             'token': os.environ.get('SPARROW_SMS_TOKEN'),
    #             'from': 'Luna IoT',
    #             'to': phone_number,
    #             'text': message
    #         }
    #     )
    #     return response.status_code == 200
    # except Exception as e:
    #     logger.error(f"SMS error: {e}")
    #     return False
    
    return True


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashcam_devices(request):
    """
    List all dashcam devices.
    
    GET /api/tcp-service/dashcam/devices/
    """
    devices = Device.objects.filter(type='dashcam').select_related('subscription_plan')
    
    data = []
    for device in devices:
        data.append({
            'id': device.id,
            'imei': device.imei,
            'phone': device.phone,
            'sim': device.sim,
            'protocol': device.protocol,
            'model': device.model,
            'type': device.type,
            'iccid': device.iccid,
            'subscription_plan': {
                'id': device.subscription_plan.id,
                'title': device.subscription_plan.title
            } if device.subscription_plan else None,
            'created_at': device.createdAt,
            'updated_at': device.updatedAt,
        })
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashcam_connection_status(request, imei):
    """
    Get connection status for a dashcam device.
    
    GET /api/tcp-service/dashcam/status/<imei>/
    """
    from .models import DashcamConnection
    from .tcp.device_manager import device_manager
    
    try:
        device = Device.objects.get(imei=imei)
    except Device.DoesNotExist:
        return Response(
            {'error': 'Device not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get connection record
    try:
        connection = DashcamConnection.objects.get(imei=imei)
        connection_data = {
            'is_connected': connection.is_connected,
            'last_heartbeat': connection.last_heartbeat,
            'connected_at': connection.connected_at,
            'ip_address': connection.ip_address,
        }
    except DashcamConnection.DoesNotExist:
        connection_data = {
            'is_connected': False,
            'last_heartbeat': None,
            'connected_at': None,
            'ip_address': None,
        }
    
    # Check in-memory status
    in_memory = device_manager.get_device(imei)
    if in_memory:
        connection_data['is_streaming'] = in_memory.get('is_streaming', False)
        connection_data['stream_channel'] = in_memory.get('stream_channel', 0)
    else:
        connection_data['is_streaming'] = False
        connection_data['stream_channel'] = 0
    
    return Response({
        'imei': imei,
        'device_info': {
            'phone': device.phone,
            'model': device.model,
            'type': device.type,
        },
        'connection': connection_data
    })
