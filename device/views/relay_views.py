"""
Relay Views
Handles relay control endpoints
Matches Node.js relay_controller.js functionality exactly
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from device.models.device import Device
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError, ValidationError
from api_common.utils.tcp_service import tcp_service


@api_view(['POST'])
@require_auth
@api_response
def turn_on_relay(request):
    """
    Turn ON relay via TCP
    Matches Node.js RelayController.turnOnRelay
    """
    try:
        data = request.data
        imei = data.get('imei')
        
        if not imei:
            return error_response(
                message='IMEI is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Check if device exists
        try:
            device = Device.objects.get(imei=imei)
        except Device.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['DEVICE_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Send relay ON command via TCP
        tcp_result = tcp_service.send_relay_on_command(imei)
        
        if tcp_result['success']:
            return success_response(
                data={
                    'imei': imei,
                    'command': 'on',
                    'status': 'sent'
                },
                message=SUCCESS_MESSAGES['RELAY_TURNED_ON_SUCCESSFULLY']
            )
        else:
            return error_response(
                message=f'Failed to send relay ON command: {tcp_result["message"]}',
                status_code=HTTP_STATUS['INTERNAL_ERROR']
            )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@api_response
def turn_off_relay(request):
    """
    Turn OFF relay via TCP
    Matches Node.js RelayController.turnOffRelay
    """
    try:
        data = request.data
        imei = data.get('imei')
        
        if not imei:
            return error_response(
                message='IMEI is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Check if device exists
        try:
            device = Device.objects.get(imei=imei)
        except Device.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['DEVICE_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Send relay OFF command via TCP
        tcp_result = tcp_service.send_relay_off_command(imei)
        
        if tcp_result['success']:
            return success_response(
                data={
                    'imei': imei,
                    'command': 'off',
                    'status': 'sent'
                },
                message=SUCCESS_MESSAGES['RELAY_TURNED_OFF_SUCCESSFULLY']
            )
        else:
            return error_response(
                message=f'Failed to send relay OFF command: {tcp_result["message"]}',
                status_code=HTTP_STATUS['INTERNAL_ERROR']
            )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )