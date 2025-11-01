"""
Device Views
Handles device management endpoints
Matches Node.js device_controller.js functionality exactly
"""
from django.http import JsonResponse
from django.core.paginator import Paginator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from device.models.device import Device
from device.models.user_device import UserDevice
from device.models.status import Status
from device.models.buzzer_status import BuzzerStatus
from device.models.sos_status import SosStatus
from core.models.user import User
from api_common.utils.response_utils import success_response, error_response
from api_common.utils.validation_utils import validate_imei
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin, require_dealer_or_admin
from api_common.exceptions.api_exceptions import NotFoundError, ValidationError
from api_common.utils.sms_service import sms_service
import requests
import logging
from django.conf import settings
from typing import Dict, Any

logger = logging.getLogger(__name__)


@api_view(['GET'])
@require_auth
@api_response
def get_all_devices(request):
    """
    Get all devices with related data
    Matches Node.js DeviceController.getAllDevices
    """
    try:
        user = request.user
        
        # Get user groups (Django's role system)
        user_groups = user.groups.all()
        is_super_admin = any(group.name == 'Super Admin' for group in user_groups)
        is_dealer = any(group.name == 'Dealer' for group in user_groups)
        
        # Super Admin: all access
        if is_super_admin:
            devices = Device.objects.prefetch_related(
                'userDevices__user__groups',
                'vehicles__userVehicles__user__groups'
            ).all()
            devices_data = []
            for device in devices:
                # Get user devices with user info and roles
                user_devices_data = []
                for user_device in device.userDevices.all():
                    user_data = {
                        'id': user_device.user.id,
                        'name': user_device.user.name,
                        'phone': user_device.user.phone,
                        'status': 'active',  # Default status
                        'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in user_device.user.groups.all()],
                        'createdAt': user_device.createdAt.isoformat(),
                        'updatedAt': user_device.createdAt.isoformat()
                    }
                    user_devices_data.append({
                        'id': user_device.id,
                        'userId': user_device.user.id,
                        'deviceId': device.id,
                        'user': user_data,
                        'createdAt': user_device.createdAt.isoformat(),
                        'updatedAt': user_device.createdAt.isoformat()
                    })
                
                # Get vehicles with user vehicles
                vehicles_data = []
                for vehicle in device.vehicles.all():
                    user_vehicles_data = []
                    for user_vehicle in vehicle.userVehicles.all():
                        user_data = {
                            'id': user_vehicle.user.id,
                            'name': user_vehicle.user.name,
                            'phone': user_vehicle.user.phone,
                            'status': 'active',  # Default status
                            'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in user_vehicle.user.groups.all()],
                            'createdAt': user_vehicle.createdAt.isoformat(),
                            'updatedAt': user_vehicle.createdAt.isoformat()
                        }
                        user_vehicles_data.append({
                            'id': user_vehicle.id,
                            'userId': user_vehicle.user.id,
                            'vehicleId': vehicle.id,
                            'isMain': user_vehicle.isMain,
                            'user': user_data,
                            'relay': getattr(user_vehicle, 'relay', False),
                            'createdAt': user_vehicle.createdAt.isoformat(),
                            'updatedAt': user_vehicle.createdAt.isoformat()
                        })
                    
                    vehicles_data.append({
                        'id': vehicle.id,
                        'imei': vehicle.imei,
                        'name': vehicle.name,
                        'vehicleNo': vehicle.vehicleNo,
                        'vehicleType': vehicle.vehicleType,
                        'userVehicles': user_vehicles_data
                    })
                
                devices_data.append({
                    'id': device.id,
                    'imei': device.imei,
                    'phone': device.phone,
                    'sim': device.sim,
                    'protocol': device.protocol,
                    'iccid': device.iccid,
                    'model': device.model,
                    'type': device.type,
                    'status': 'active',  # Default status
                    'subscription_plan': {
                        'id': device.subscription_plan.id,
                        'title': device.subscription_plan.title,
                        'price': float(device.subscription_plan.price)
                    } if device.subscription_plan else None,
                    'userDevices': user_devices_data,
                    'vehicles': vehicles_data,
                    'createdAt': device.createdAt.isoformat(),
                    'updatedAt': device.updatedAt.isoformat()
                })
            return success_response(
                data=devices_data,
                message=SUCCESS_MESSAGES['DEVICES_RETRIEVED']
            )
        
        # Dealer: only view assigned devices
        elif is_dealer:
            user_devices = UserDevice.objects.filter(user=user).select_related('device').prefetch_related(
                'device__userDevices__user__groups',
                'device__vehicles__userVehicles__user__groups'
            )
            devices_data = []
            for user_device in user_devices:
                device = user_device.device
                
                # Get user devices with user info and roles
                user_devices_data = []
                for ud in device.userDevices.all():
                    user_data = {
                        'id': ud.user.id,
                        'name': ud.user.name,
                        'phone': ud.user.phone,
                        'status': 'active',  # Default status
                        'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in ud.user.groups.all()],
                        'createdAt': ud.createdAt.isoformat(),
                        'updatedAt': ud.createdAt.isoformat()
                    }
                    user_devices_data.append({
                        'id': ud.id,
                        'userId': ud.user.id,
                        'deviceId': device.id,
                        'user': user_data,
                        'createdAt': ud.createdAt.isoformat(),
                        'updatedAt': ud.createdAt.isoformat()
                    })
                
                # Get vehicles with user vehicles
                vehicles_data = []
                for vehicle in device.vehicles.all():
                    user_vehicles_data = []
                    for user_vehicle in vehicle.userVehicles.all():
                        user_data = {
                            'id': user_vehicle.user.id,
                            'name': user_vehicle.user.name,
                            'phone': user_vehicle.user.phone,
                            'status': 'active',  # Default status
                            'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in user_vehicle.user.groups.all()],
                            'createdAt': user_vehicle.createdAt.isoformat(),
                            'updatedAt': user_vehicle.createdAt.isoformat()
                        }
                        user_vehicles_data.append({
                            'id': user_vehicle.id,
                            'userId': user_vehicle.user.id,
                            'vehicleId': vehicle.id,
                            'isMain': user_vehicle.isMain,
                            'user': user_data,
                            'createdAt': user_vehicle.createdAt.isoformat(),
                            'updatedAt': user_vehicle.createdAt.isoformat()
                        })
                    
                    vehicles_data.append({
                        'id': vehicle.id,
                        'imei': vehicle.imei,
                        'name': vehicle.name,
                        'vehicleNo': vehicle.vehicleNo,
                        'vehicleType': vehicle.vehicleType,
                        'userVehicles': user_vehicles_data
                    })
                
                devices_data.append({
                    'id': device.id,
                    'imei': device.imei,
                    'phone': device.phone,
                    'sim': device.sim,
                    'protocol': device.protocol,
                    'iccid': device.iccid,
                    'model': device.model,
                    'type': device.type,
                    'status': 'active',  # Default status
                    'subscription_plan': {
                        'id': device.subscription_plan.id,
                        'title': device.subscription_plan.title,
                        'price': float(device.subscription_plan.price)
                    } if device.subscription_plan else None,
                    'userDevices': user_devices_data,
                    'vehicles': vehicles_data,
                    'createdAt': device.createdAt.isoformat(),
                    'updatedAt': device.updatedAt.isoformat()
                })
            return success_response(
                data=devices_data,
                message='Dealer devices retrieved successfully'
            )
        
        # Customer: no access to devices
        else:
            return error_response(
                message='Access denied. Customers cannot view devices',
                status_code=HTTP_STATUS['FORBIDDEN']
            )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_device_by_imei(request, imei):
    """
    Get device by IMEI
    Matches Node.js DeviceController.getDeviceByImei
    """
    try:
        user = request.user
        
        # Get user groups (Django's role system)
        user_groups = user.groups.all()
        is_super_admin = any(group.name == 'Super Admin' for group in user_groups)
        is_dealer = any(group.name == 'Dealer' for group in user_groups)
        
        # Super Admin: can access any device
        if is_super_admin:
            try:
                device = Device.objects.prefetch_related(
                    'userDevices__user__groups',
                    'vehicles__userVehicles__user__groups'
                ).get(imei=imei)
            except Device.DoesNotExist:
                return error_response(
                    message=ERROR_MESSAGES['DEVICE_NOT_FOUND'],
                    status_code=HTTP_STATUS['NOT_FOUND']
                )
        
        # Dealer: can only access assigned devices
        elif is_dealer:
            try:
                user_device = UserDevice.objects.select_related('device').prefetch_related(
                    'device__userDevices__user__groups',
                    'device__vehicles__userVehicles__user__groups'
                ).get(
                    user=user,
                    device__imei=imei
                )
                device = user_device.device
            except UserDevice.DoesNotExist:
                return error_response(
                    message='Device not found or access denied',
                    status_code=HTTP_STATUS['NOT_FOUND']
                )
        
        # Customer: no access to devices
        else:
            return error_response(
                message='Access denied. Customers cannot view devices',
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        # Get user devices with user info and roles
        user_devices_data = []
        for user_device in device.userDevices.all():
            user_data = {
                'id': user_device.user.id,
                'name': user_device.user.name,
                'phone': user_device.user.phone,
                'status': 'active',  # Default status
                'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in user_device.user.groups.all()],
                'createdAt': user_device.createdAt.isoformat(),
                'updatedAt': user_device.createdAt.isoformat()
            }
            user_devices_data.append({
                'id': user_device.id,
                'userId': user_device.user.id,
                'deviceId': device.id,
                'user': user_data,
                'createdAt': user_device.createdAt.isoformat(),
                'updatedAt': user_device.createdAt.isoformat()
            })
        
        # Get vehicles with user vehicles
        vehicles_data = []
        for vehicle in device.vehicles.all():
            user_vehicles_data = []
            for user_vehicle in vehicle.userVehicles.all():
                user_data = {
                    'id': user_vehicle.user.id,
                    'name': user_vehicle.user.name,
                    'phone': user_vehicle.user.phone,
                    'status': 'active',  # Default status
                    'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in user_vehicle.user.groups.all()],
                    'createdAt': user_vehicle.createdAt.isoformat(),
                    'updatedAt': user_vehicle.createdAt.isoformat()
                }
                user_vehicles_data.append({
                    'id': user_vehicle.id,
                    'userId': user_vehicle.user.id,
                    'vehicleId': vehicle.id,
                    'isMain': user_vehicle.isMain,
                    'user': user_data,
                    'relay': getattr(user_vehicle, 'relay', False),
                    'createdAt': user_vehicle.createdAt.isoformat(),
                    'updatedAt': user_vehicle.createdAt.isoformat()
                })
            
            vehicles_data.append({
                'id': vehicle.id,
                'imei': vehicle.imei,
                'name': vehicle.name,
                'vehicleNo': vehicle.vehicleNo,
                'vehicleType': vehicle.vehicleType,
                'userVehicles': user_vehicles_data
            })
        
        device_data = {
            'id': device.id,
            'imei': device.imei,
            'phone': device.phone,
            'sim': device.sim,
            'protocol': device.protocol,
            'iccid': device.iccid,
            'model': device.model,
            'type': device.type,
            'status': 'active',  # Default status
            'subscription_plan': {
                'id': device.subscription_plan.id,
                'title': device.subscription_plan.title,
                'price': float(device.subscription_plan.price)
            } if device.subscription_plan else None,
            'userDevices': user_devices_data,
            'vehicles': vehicles_data,
            'createdAt': device.createdAt.isoformat(),
            'updatedAt': device.updatedAt.isoformat()
        }
        
        return success_response(
            data=device_data,
            message=SUCCESS_MESSAGES['DEVICE_RETRIEVED']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_super_admin
@api_response
def create_device(request):
    """
    Create new device (only Super Admin)
    Matches Node.js DeviceController.createDevice
    """
    try:
        data = request.data
        
        # Handle subscription_plan foreign key
        subscription_plan_id = data.pop('subscription_plan', None)
        if subscription_plan_id is not None:
            try:
                from device.models import SubscriptionPlan
                subscription_plan = SubscriptionPlan.objects.get(id=subscription_plan_id)
                data['subscription_plan'] = subscription_plan
            except SubscriptionPlan.DoesNotExist:
                return error_response(
                    message=f"Subscription plan with ID {subscription_plan_id} not found",
                    status_code=HTTP_STATUS['BAD_REQUEST']
                )
        
        device = Device.objects.create(**data)
        
        device_data = {
            'id': device.id,
            'imei': device.imei,
            'phone': device.phone,
            'sim': device.sim,
            'protocol': device.protocol,
            'iccid': device.iccid,
            'model': device.model,
            'type': device.type,
            'subscription_plan': {
                'id': device.subscription_plan.id,
                'title': device.subscription_plan.title,
                'price': float(device.subscription_plan.price)
            } if device.subscription_plan else None,
            'createdAt': device.createdAt.isoformat(),
            'updatedAt': device.updatedAt.isoformat()
        }
        
        return success_response(
            data=device_data,
            message=SUCCESS_MESSAGES['DEVICE_CREATED'],
            status_code=HTTP_STATUS['CREATED']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['PUT'])
@require_super_admin
@api_response
def update_device(request, imei):
    """
    Update device (only Super Admin)
    Matches Node.js DeviceController.updateDevice
    """
    try:
        data = request.data
        
        try:
            device = Device.objects.get(imei=imei)
        except Device.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['DEVICE_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Update device fields
        for key, value in data.items():
            if hasattr(device, key):
                if key == 'subscription_plan':
                    # Handle subscription_plan foreign key
                    if value is None:
                        device.subscription_plan = None
                    else:
                        try:
                            from device.models import SubscriptionPlan
                            subscription_plan = SubscriptionPlan.objects.get(id=value)
                            device.subscription_plan = subscription_plan
                        except SubscriptionPlan.DoesNotExist:
                            return error_response(
                                message=f"Subscription plan with ID {value} not found",
                                status_code=HTTP_STATUS['BAD_REQUEST']
                            )
                else:
                    setattr(device, key, value)
        
        device.save()
        
        device_data = {
            'id': device.id,
            'imei': device.imei,
            'phone': device.phone,
            'sim': device.sim,
            'protocol': device.protocol,
            'iccid': device.iccid,
            'model': device.model,
            'type': device.type,
            'subscription_plan': {
                'id': device.subscription_plan.id,
                'title': device.subscription_plan.title,
                'price': float(device.subscription_plan.price)
            } if device.subscription_plan else None,
            'createdAt': device.createdAt.isoformat(),
            'updatedAt': device.updatedAt.isoformat()
        }
        
        return success_response(
            data=device_data,
            message=SUCCESS_MESSAGES['DEVICE_UPDATED']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['DELETE'])
@require_super_admin
@api_response
def delete_device(request, imei):
    """
    Delete device (only Super Admin)
    Matches Node.js DeviceController.deleteDevice
    """
    try:
        try:
            device = Device.objects.get(imei=imei)
        except Device.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['DEVICE_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        device.delete()
        
        return success_response(
            message=SUCCESS_MESSAGES['DEVICE_DELETED']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_super_admin
@api_response
def assign_device_to_user(request):
    """
    Assign device to user
    Matches Node.js DeviceController.assignDeviceToUser
    """
    try:
        data = request.data
        imei = data.get('imei')
        user_phone = data.get('userPhone')
        
        if not imei or not user_phone:
            return error_response(
                message='IMEI and user phone are required',
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
        
        # Check if user exists and is a dealer
        try:
            target_user = User.objects.prefetch_related('groups').get(phone=user_phone)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Check if user is a dealer
        target_user_groups = target_user.groups.all()
        is_dealer = any(group.name == 'Dealer' for group in target_user_groups)
        
        if not is_dealer:
            return error_response(
                message='Only dealers can be assigned devices',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Check if already assigned
        if UserDevice.objects.filter(user=target_user, device=device).exists():
            return error_response(
                message='Device is already assigned to this user',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Assign device to user
        assignment = UserDevice.objects.create(user=target_user, device=device)
        
        return success_response(
            data={
                'id': assignment.id,
                'userId': target_user.id,
                'deviceId': device.id,
                'imei': device.imei,
                'userPhone': target_user.phone
            },
            message='Device assigned successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['DELETE'])
@require_super_admin
@api_response
def remove_device_assignment(request):
    """
    Remove device assignment
    Matches Node.js DeviceController.removeDeviceAssignment
    """
    try:
        data = request.data
        imei = data.get('imei')
        user_phone = data.get('userPhone')
        
        if not imei or not user_phone:
            return error_response(
                message='IMEI and user phone are required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Check if user exists
        try:
            target_user = User.objects.get(phone=user_phone)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Check if device exists
        try:
            device = Device.objects.get(imei=imei)
        except Device.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['DEVICE_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Remove device assignment
        deleted_count, _ = UserDevice.objects.filter(
            user=target_user,
            device=device
        ).delete()
        
        if deleted_count > 0:
            return success_response(
                message='Device assignment removed successfully'
            )
        else:
            return error_response(
                message='Device assignment not found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_super_admin
@api_response
def send_server_point(request):
    """
    Send server point command via SMS
    Matches Node.js DeviceController.sendServerPoint
    """
    try:
        data = request.data
        phone = data.get('phone')
        
        if not phone:
            return error_response(
                message='Phone number is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Server point command message
        server_point_message = 'SERVER,0,38.54.71.218,6666,0#'
        
        # Send SMS using SMS service
        sms_result = sms_service.send_server_point_command(phone)
        
        if sms_result['success']:
            return success_response(
                data={
                    'phone': phone,
                    'message': server_point_message,
                    'sent': True
                },
                message='Server point command sent successfully'
            )
        else:
            return error_response(
                message=f'Failed to send server point command: {sms_result["message"]}',
                status_code=HTTP_STATUS['INTERNAL_ERROR']
            )
            
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_super_admin
@api_response
def send_reset(request):
    """
    Send reset command via SMS
    Matches Node.js DeviceController.sendReset
    """
    try:
        data = request.data
        phone = data.get('phone')
        
        if not phone:
            return error_response(
                message='Phone number is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Reset command message
        reset_message = 'RESET#'
        
        # Send SMS using SMS service
        sms_result = sms_service.send_reset_command(phone)
        
        if sms_result['success']:
            return success_response(
                data={
                    'phone': phone,
                    'message': reset_message,
                    'sent': True
                },
                message='Reset command sent successfully'
            )
        else:
            return error_response(
                message=f'Failed to send reset command: {sms_result["message"]}',
                status_code=HTTP_STATUS['INTERNAL_ERROR']
            )
            
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


def send_tcp_relay_command(phone: str, command: str) -> Dict[str, Any]:
    """
    Send relay command via TCP (Node.js API)
    This replaces SMS commands with direct TCP connection
    
    Args:
        phone: Device phone number
        command: 'ON' or 'OFF'
    
    Returns:
        Dict with success status and result/error
    """
    try:
        logger.info(f'[RELAY TCP] Starting relay command via TCP - Phone: {phone}, Command: {command}')
        
        # Get device by phone to get IMEI
        try:
            device = Device.objects.get(phone=phone)
            imei = device.imei
            logger.info(f'[RELAY TCP] Device found - Phone: {phone}, IMEI: {imei}')
        except Device.DoesNotExist:
            logger.error(f'[RELAY TCP] Device not found for phone: {phone}')
            return {'success': False, 'error': 'Device not found'}
        
        # Get Node.js API URL
        nodejs_base_url = getattr(settings, 'NODEJS_API_BASE_URL', 'http://localhost:6060')
        nodejs_url = f"{nodejs_base_url}/api/tcp/send-command"
        
        # Prepare payload
        payload = {
            'imei': imei,
            'commandType': 'RELAY',
            'params': {'command': command}
        }
        
        logger.info(f'[RELAY TCP] Calling Node.js TCP API - URL: {nodejs_url}, Payload: {payload}')
        
        # Call Node.js TCP API
        try:
            response = requests.post(nodejs_url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            logger.info(f'[RELAY TCP] Node.js API response - Success: {result.get("success")}, Queued: {result.get("queued", False)}, Message: {result.get("message")}')
            
            return result
        except requests.exceptions.Timeout:
            logger.error(f'[RELAY TCP] Node.js API timeout for device {imei}')
            return {'success': False, 'error': 'TCP API timeout - request took too long'}
        except requests.exceptions.ConnectionError:
            logger.error(f'[RELAY TCP] Node.js API connection error for device {imei}')
            return {'success': False, 'error': 'TCP API connection error - unable to reach Node.js server'}
        except requests.exceptions.RequestException as e:
            logger.error(f'[RELAY TCP] Node.js API request error for device {imei}: {str(e)}')
            return {'success': False, 'error': f'TCP API request error: {str(e)}'}
        except Exception as e:
            logger.error(f'[RELAY TCP] Unexpected error calling Node.js API for device {imei}: {str(e)}')
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
            
    except Exception as e:
        logger.error(f'[RELAY TCP] Unexpected error in send_tcp_relay_command: {str(e)}')
        return {'success': False, 'error': str(e)}


@api_view(['POST'])
@require_auth
@api_response
def send_relay_on(request):
    """
    Send relay ON command via TCP (Node.js API)
    SMS service kept available as fallback but not used
    Matches Node.js DeviceController.sendRelayOn
    """
    try:
        data = request.data
        phone = data.get('phone')
        
        logger.info(f'[RELAY ON] Received request - Phone: {phone}, User: {request.user.phone if request.user else "Anonymous"}')
        
        if not phone:
            logger.warning('[RELAY ON] Phone number not provided in request')
            return error_response(
                message='Phone number is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Send relay command via TCP (Node.js API)
        tcp_result = send_tcp_relay_command(phone, 'ON')
        
        if tcp_result.get('success'):
            queued = tcp_result.get('queued', False)
            logger.info(f'[RELAY ON] Command successful - Phone: {phone}, Queued: {queued}')
            
            return success_response(
                data={
                    'phone': phone,
                    'command': 'ON',
                    'queued': queued,
                    'sent': True
                },
                message='Relay ON command sent successfully' if not queued else 'Relay ON command queued - will be sent when device connects'
            )
        else:
            error_msg = tcp_result.get('error', 'Unknown error')
            logger.error(f'[RELAY ON] Command failed - Phone: {phone}, Error: {error_msg}')
            
            # SMS fallback option (commented out, can be enabled if needed)
            # relay_on_message = 'RELAY,1#'
            # sms_result = sms_service.send_relay_on_command(phone)
            # if sms_result['success']:
            #     return success_response(...)
            
            return error_response(
                message=f'Failed to send relay ON command: {error_msg}',
                status_code=HTTP_STATUS['INTERNAL_ERROR']
            )
            
    except Exception as e:
        logger.error(f'[RELAY ON] Unexpected error: {str(e)}', exc_info=True)
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@api_response
def send_relay_off(request):
    """
    Send relay OFF command via TCP (Node.js API)
    SMS service kept available as fallback but not used
    Matches Node.js DeviceController.sendRelayOff
    """
    try:
        data = request.data
        phone = data.get('phone')
        
        logger.info(f'[RELAY OFF] Received request - Phone: {phone}, User: {request.user.phone if request.user else "Anonymous"}')
        
        if not phone:
            logger.warning('[RELAY OFF] Phone number not provided in request')
            return error_response(
                message='Phone number is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Send relay command via TCP (Node.js API)
        tcp_result = send_tcp_relay_command(phone, 'OFF')
        
        if tcp_result.get('success'):
            queued = tcp_result.get('queued', False)
            logger.info(f'[RELAY OFF] Command successful - Phone: {phone}, Queued: {queued}')
            
            return success_response(
                data={
                    'phone': phone,
                    'command': 'OFF',
                    'queued': queued,
                    'sent': True
                },
                message='Relay OFF command sent successfully' if not queued else 'Relay OFF command queued - will be sent when device connects'
            )
        else:
            error_msg = tcp_result.get('error', 'Unknown error')
            logger.error(f'[RELAY OFF] Command failed - Phone: {phone}, Error: {error_msg}')
            
            # SMS fallback option (commented out, can be enabled if needed)
            # relay_off_message = 'RELAY,0#'
            # sms_result = sms_service.send_relay_off_command(phone)
            # if sms_result['success']:
            #     return success_response(...)
            
            return error_response(
                message=f'Failed to send relay OFF command: {error_msg}',
                status_code=HTTP_STATUS['INTERNAL_ERROR']
            )
            
    except Exception as e:
        logger.error(f'[RELAY OFF] Unexpected error: {str(e)}', exc_info=True)
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_devices_paginated(request):
    """
    Get paginated devices with related data
    """
    try:
        user = request.user
        
        # Get page number from query parameters, default to 1
        page_number = int(request.GET.get('page', 1))
        page_size = 25  # Fixed page size as requested
        
        # Get user groups (Django's role system)
        user_groups = user.groups.all()
        is_super_admin = any(group.name == 'Super Admin' for group in user_groups)
        is_dealer = any(group.name == 'Dealer' for group in user_groups)
        
        # Super Admin: all access
        if is_super_admin:
            devices = Device.objects.prefetch_related(
                'userDevices__user__groups',
                'vehicles__userVehicles__user__groups',
                'subscription_plan'
            ).all()
        # Dealer: only view assigned devices
        elif is_dealer:
            user_devices = UserDevice.objects.filter(user=user).select_related('device').prefetch_related(
                'device__userDevices__user__groups',
                'device__vehicles__userVehicles__user__groups',
                'device__subscription_plan'
            )
            devices = [ud.device for ud in user_devices]
        # Customer: no access to devices
        else:
            return error_response(
                message='Access denied. Customers cannot view devices',
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        # Create paginator
        paginator = Paginator(devices, page_size)
        
        # Get the requested page
        try:
            page_obj = paginator.get_page(page_number)
        except:
            return error_response('Invalid page number', HTTP_STATUS['BAD_REQUEST'])
        
        devices_data = []
        for device in page_obj:
            # Get user devices with user info and roles
            user_devices_data = []
            for user_device in device.userDevices.all():
                user_data = {
                    'id': user_device.user.id,
                    'name': user_device.user.name,
                    'phone': user_device.user.phone,
                    'status': 'active',  # Default status
                    'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in user_device.user.groups.all()],
                    'createdAt': user_device.createdAt.isoformat(),
                    'updatedAt': user_device.createdAt.isoformat()
                }
                user_devices_data.append({
                    'id': user_device.id,
                    'userId': user_device.user.id,
                    'deviceId': device.id,
                    'user': user_data,
                    'createdAt': user_device.createdAt.isoformat(),
                    'updatedAt': user_device.createdAt.isoformat()
                })
            
            # Get vehicles with user vehicles
            vehicles_data = []
            for vehicle in device.vehicles.all():
                user_vehicles_data = []
                for user_vehicle in vehicle.userVehicles.all():
                    user_data = {
                        'id': user_vehicle.user.id,
                        'name': user_vehicle.user.name,
                        'phone': user_vehicle.user.phone,
                        'status': 'active',  # Default status
                        'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in user_vehicle.user.groups.all()],
                        'createdAt': user_vehicle.createdAt.isoformat(),
                        'updatedAt': user_vehicle.createdAt.isoformat()
                    }
                    user_vehicles_data.append({
                        'id': user_vehicle.id,
                        'userId': user_vehicle.user.id,
                        'vehicleId': vehicle.id,
                        'isMain': user_vehicle.isMain,
                        'user': user_data,
                        'relay': getattr(user_vehicle, 'relay', False),
                        'createdAt': user_vehicle.createdAt.isoformat(),
                        'updatedAt': user_vehicle.createdAt.isoformat()
                    })
                
                vehicles_data.append({
                    'id': vehicle.id,
                    'imei': vehicle.imei,
                    'name': vehicle.name,
                    'vehicleNo': vehicle.vehicleNo,
                    'vehicleType': vehicle.vehicleType,
                    'userVehicles': user_vehicles_data
                })
            
            # Get latest status based on device type
            latest_status = None
            device_type = (device.type or 'gps').lower()
            try:
                if device_type == 'sos':
                    latest_status_obj = SosStatus.objects.filter(imei=device.imei).order_by('-createdAt', '-updatedAt').first()
                elif device_type == 'buzzer':
                    latest_status_obj = BuzzerStatus.objects.filter(imei=device.imei).order_by('-createdAt', '-updatedAt').first()
                else:
                    # Default to GPS status
                    latest_status_obj = Status.objects.filter(imei=device.imei).order_by('-createdAt', '-updatedAt').first()
                
                if latest_status_obj:
                    latest_status = {
                        'id': latest_status_obj.id,
                        'imei': latest_status_obj.imei,
                        'battery': latest_status_obj.battery,
                        'signal': latest_status_obj.signal,
                        'ignition': latest_status_obj.ignition,
                        'charging': latest_status_obj.charging,
                        'relay': latest_status_obj.relay,
                        'createdAt': latest_status_obj.createdAt.isoformat(),
                        'updatedAt': latest_status_obj.updatedAt.isoformat() if hasattr(latest_status_obj, 'updatedAt') and latest_status_obj.updatedAt else latest_status_obj.createdAt.isoformat()
                    }
            except Exception as e:
                latest_status = None
            
            devices_data.append({
                'id': device.id,
                'imei': device.imei,
                'phone': device.phone,
                'sim': device.sim,
                'protocol': device.protocol,
                'iccid': device.iccid,
                'model': device.model,
                'type': device.type,
                'status': 'active',  # Default status
                'subscription_plan': {
                    'id': device.subscription_plan.id,
                    'title': device.subscription_plan.title,
                    'price': float(device.subscription_plan.price)
                } if device.subscription_plan else None,
                'userDevices': user_devices_data,
                'vehicles': vehicles_data,
                'latestStatus': latest_status,
                'createdAt': device.createdAt.isoformat(),
                'updatedAt': device.updatedAt.isoformat()
            })
        
        # Prepare pagination info
        pagination_info = {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None
        }
        
        response_data = {
            'devices': devices_data,
            'pagination': pagination_info
        }
        
        return success_response(
            data=response_data,
            message='Paginated devices retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def search_devices(request):
    """
    Search devices with multiple fields: device imei, phone, protocol, sim, model, 
    related vehicle (vehicle no and vehicle name), related user (name and phone),
    and users related to vehicles (name and phone)
    Supports pagination with page parameter
    """
    try:
        from django.db.models import Q
        from django.core.paginator import Paginator
        
        user = request.user
        search_query = request.GET.get('q', '').strip()
        page_number = int(request.GET.get('page', 1))
        page_size = 25  # Fixed page size
        
        if not search_query:
            return error_response('Search query is required', HTTP_STATUS['BAD_REQUEST'])
        
        # Get user groups (Django's role system)
        user_groups = user.groups.all()
        is_super_admin = any(group.name == 'Super Admin' for group in user_groups)
        is_dealer = any(group.name == 'Dealer' for group in user_groups)
        
        # Super Admin: all access
        if is_super_admin:
            devices = Device.objects.prefetch_related(
                'userDevices__user__groups',
                'vehicles__userVehicles__user__groups',
                'subscription_plan'
            ).all()
        # Dealer: devices assigned to them
        elif is_dealer:
            devices = Device.objects.filter(
                userDevices__user=user
            ).prefetch_related(
                'userDevices__user__groups',
                'vehicles__userVehicles__user__groups',
                'subscription_plan'
            ).distinct()
        # Regular user: devices assigned to them
        else:
            devices = Device.objects.filter(
                userDevices__user=user
            ).prefetch_related(
                'userDevices__user__groups',
                'vehicles__userVehicles__user__groups',
                'subscription_plan'
            ).distinct()
        
        # Apply search filters
        search_filter = Q()
        
        # Search in device fields
        search_filter |= Q(imei__icontains=search_query)
        search_filter |= Q(phone__icontains=search_query)
        search_filter |= Q(protocol__icontains=search_query)
        search_filter |= Q(sim__icontains=search_query)
        search_filter |= Q(model__icontains=search_query)
        search_filter |= Q(iccid__icontains=search_query)
        
        # Search in related users (name and phone)
        search_filter |= Q(userDevices__user__name__icontains=search_query)
        search_filter |= Q(userDevices__user__phone__icontains=search_query)
        
        # Search in related vehicles (vehicle no and vehicle name)
        search_filter |= Q(vehicles__vehicleNo__icontains=search_query)
        search_filter |= Q(vehicles__name__icontains=search_query)
        
        # Search in users related to vehicles (name and phone)
        search_filter |= Q(vehicles__userVehicles__user__name__icontains=search_query)
        search_filter |= Q(vehicles__userVehicles__user__phone__icontains=search_query)
        
        # Apply the search filter
        devices = devices.filter(search_filter).distinct()
        
        # Create paginator
        paginator = Paginator(devices, page_size)
        
        # Get the requested page
        try:
            page_obj = paginator.get_page(page_number)
        except:
            return error_response('Invalid page number', HTTP_STATUS['BAD_REQUEST'])
        
        devices_data = []
        for device in page_obj:
            # Get user devices with user info and roles
            user_devices_data = []
            for user_device in device.userDevices.all():
                user_data = {
                    'id': user_device.user.id,
                    'name': user_device.user.name,
                    'phone': user_device.user.phone,
                    'status': 'active',  # Default status
                    'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in user_device.user.groups.all()],
                    'createdAt': user_device.createdAt.isoformat(),
                    'updatedAt': user_device.createdAt.isoformat()
                }
                
                user_devices_data.append({
                    'id': user_device.id,
                    'userId': user_device.user.id,
                    'deviceId': device.id,
                    'user': user_data,
                    'createdAt': user_device.createdAt.isoformat(),
                    'updatedAt': user_device.createdAt.isoformat()
                })
            
            # Get vehicles with user info
            vehicles_data = []
            for vehicle in device.vehicles.all():
                user_vehicles_data = []
                for user_vehicle in vehicle.userVehicles.all():
                    user_data = {
                        'id': user_vehicle.user.id,
                        'name': user_vehicle.user.name,
                        'phone': user_vehicle.user.phone,
                        'status': 'active',  # Default status
                        'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in user_vehicle.user.groups.all()],
                        'createdAt': user_vehicle.createdAt.isoformat(),
                        'updatedAt': user_vehicle.createdAt.isoformat()
                    }
                    
                    user_vehicles_data.append({
                        'id': user_vehicle.id,
                        'userId': user_vehicle.user.id,
                        'vehicleId': vehicle.id,
                        'isMain': user_vehicle.isMain,
                        'user': user_data,
                        'createdAt': user_vehicle.createdAt.isoformat(),
                        'updatedAt': user_vehicle.createdAt.isoformat()
                    })
                
                vehicles_data.append({
                    'id': vehicle.id,
                    'imei': vehicle.imei,
                    'name': vehicle.name,
                    'vehicleNo': vehicle.vehicleNo,
                    'vehicleType': vehicle.vehicleType,
                    'userVehicles': user_vehicles_data
                })
            
            # Get latest status based on device type
            latest_status = None
            device_type = (device.type or 'gps').lower()
            try:
                if device_type == 'sos':
                    latest_status_obj = SosStatus.objects.filter(imei=device.imei).order_by('-createdAt', '-updatedAt').first()
                elif device_type == 'buzzer':
                    latest_status_obj = BuzzerStatus.objects.filter(imei=device.imei).order_by('-createdAt', '-updatedAt').first()
                else:
                    # Default to GPS status
                    latest_status_obj = Status.objects.filter(imei=device.imei).order_by('-createdAt', '-updatedAt').first()
                
                if latest_status_obj:
                    latest_status = {
                        'id': latest_status_obj.id,
                        'imei': latest_status_obj.imei,
                        'battery': latest_status_obj.battery,
                        'signal': latest_status_obj.signal,
                        'ignition': latest_status_obj.ignition,
                        'charging': latest_status_obj.charging,
                        'relay': latest_status_obj.relay,
                        'createdAt': latest_status_obj.createdAt.isoformat(),
                        'updatedAt': latest_status_obj.updatedAt.isoformat() if hasattr(latest_status_obj, 'updatedAt') and latest_status_obj.updatedAt else latest_status_obj.createdAt.isoformat()
                    }
            except Exception as e:
                latest_status = None
            
            devices_data.append({
                'id': device.id,
                'imei': device.imei,
                'phone': device.phone,
                'sim': device.sim,
                'protocol': device.protocol,
                'iccid': device.iccid,
                'model': device.model,
                'type': device.type,
                'status': 'active',  # Default status
                'subscription_plan': {
                    'id': device.subscription_plan.id,
                    'title': device.subscription_plan.title,
                    'price': float(device.subscription_plan.price)
                } if device.subscription_plan else None,
                'userDevices': user_devices_data,
                'vehicles': vehicles_data,
                'latestStatus': latest_status,
                'createdAt': device.createdAt.isoformat(),
                'updatedAt': device.updatedAt.isoformat()
            })
        
        # Prepare pagination info
        pagination_info = {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None
        }
        
        response_data = {
            'devices': devices_data,
            'pagination': pagination_info
        }
        
        return success_response(
            data=response_data,
            message=f'Found {paginator.count} devices matching "{search_query}"'
        )
    
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_light_devices(request):
    """
    Get light device data for dropdown lists (recharge select)
    Returns only essential fields: id, imei, phone, sim, protocol, model
    """
    try:
        user = request.user
        
        # Get user groups (Django's role system)
        user_groups = user.groups.all()
        is_super_admin = any(group.name == 'Super Admin' for group in user_groups)
        is_dealer = any(group.name == 'Dealer' for group in user_groups)
        
        # Super Admin: all access
        if is_super_admin:
            devices = Device.objects.values(
                'id', 'imei', 'phone', 'sim', 'protocol', 'model'
            ).order_by('imei')
        # Dealer: only view assigned devices
        elif is_dealer:
            devices = Device.objects.filter(
                userDevices__user=user
            ).values(
                'id', 'imei', 'phone', 'sim', 'protocol', 'model'
            ).distinct().order_by('imei')
        # Customer: no access to devices
        else:
            return error_response(
                message='Access denied. Customers cannot view devices',
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        devices_list = list(devices)
        
        return success_response(
            data=devices_list,
            message='Light devices retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_gps_devices_paginated(request):
    """
    Get paginated GPS devices with search functionality
    """
    try:
        from django.db.models import Q
        from django.core.paginator import Paginator
        
        user = request.user
        search_query = request.GET.get('q', '').strip()
        page_number = int(request.GET.get('page', 1))
        page_size = 25  # Fixed page size
        
        # Get user groups (Django's role system)
        user_groups = user.groups.all()
        is_super_admin = any(group.name == 'Super Admin' for group in user_groups)
        is_dealer = any(group.name == 'Dealer' for group in user_groups)
        
        # Super Admin: all GPS devices
        if is_super_admin:
            devices = Device.objects.filter(type='gps').prefetch_related(
                'userDevices__user__groups',
                'vehicles__userVehicles__user__groups',
                'subscription_plan'
            ).all()
        # Dealer: only assigned GPS devices
        elif is_dealer:
            devices = Device.objects.filter(
                type='gps',
                userDevices__user=user
            ).prefetch_related(
                'userDevices__user__groups',
                'vehicles__userVehicles__user__groups',
                'subscription_plan'
            ).distinct()
        # Customer: no access to devices
        else:
            return error_response(
                message='Access denied. Customers cannot view devices',
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        # Apply search filter if query provided
        if search_query:
            search_filter = Q()
            search_filter |= Q(imei__icontains=search_query)
            search_filter |= Q(phone__icontains=search_query)
            search_filter |= Q(protocol__icontains=search_query)
            search_filter |= Q(sim__icontains=search_query)
            search_filter |= Q(model__icontains=search_query)
            search_filter |= Q(iccid__icontains=search_query)
            search_filter |= Q(userDevices__user__name__icontains=search_query)
            search_filter |= Q(userDevices__user__phone__icontains=search_query)
            search_filter |= Q(vehicles__vehicleNo__icontains=search_query)
            search_filter |= Q(vehicles__name__icontains=search_query)
            search_filter |= Q(vehicles__userVehicles__user__name__icontains=search_query)
            search_filter |= Q(vehicles__userVehicles__user__phone__icontains=search_query)
            devices = devices.filter(search_filter).distinct()
        
        # Create paginator
        paginator = Paginator(devices, page_size)
        
        # Get the requested page
        try:
            page_obj = paginator.get_page(page_number)
        except:
            return error_response('Invalid page number', HTTP_STATUS['BAD_REQUEST'])
        
        devices_data = []
        for device in page_obj:
            # Get user devices with user info and roles
            user_devices_data = []
            for user_device in device.userDevices.all():
                user_data = {
                    'id': user_device.user.id,
                    'name': user_device.user.name,
                    'phone': user_device.user.phone,
                    'status': 'active',  # Default status
                    'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in user_device.user.groups.all()],
                    'createdAt': user_device.createdAt.isoformat(),
                    'updatedAt': user_device.createdAt.isoformat()
                }
                user_devices_data.append({
                    'id': user_device.id,
                    'userId': user_device.user.id,
                    'deviceId': device.id,
                    'user': user_data,
                    'createdAt': user_device.createdAt.isoformat(),
                    'updatedAt': user_device.createdAt.isoformat()
                })
            
            # Get vehicles with user vehicles
            vehicles_data = []
            for vehicle in device.vehicles.all():
                user_vehicles_data = []
                for user_vehicle in vehicle.userVehicles.all():
                    user_data = {
                        'id': user_vehicle.user.id,
                        'name': user_vehicle.user.name,
                        'phone': user_vehicle.user.phone,
                        'status': 'active',  # Default status
                        'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in user_vehicle.user.groups.all()],
                        'createdAt': user_vehicle.createdAt.isoformat(),
                        'updatedAt': user_vehicle.createdAt.isoformat()
                    }
                    user_vehicles_data.append({
                        'id': user_vehicle.id,
                        'userId': user_vehicle.user.id,
                        'vehicleId': vehicle.id,
                        'isMain': user_vehicle.isMain,
                        'user': user_data,
                        'relay': getattr(user_vehicle, 'relay', False),
                        'createdAt': user_vehicle.createdAt.isoformat(),
                        'updatedAt': user_vehicle.createdAt.isoformat()
                    })
                
                vehicles_data.append({
                    'id': vehicle.id,
                    'imei': vehicle.imei,
                    'name': vehicle.name,
                    'vehicleNo': vehicle.vehicleNo,
                    'vehicleType': vehicle.vehicleType,
                    'userVehicles': user_vehicles_data
                })
            
            # Get latest status for GPS device (Status table)
            latest_status = None
            try:
                latest_status_obj = Status.objects.filter(imei=device.imei).order_by('-createdAt', '-updatedAt').first()
                if latest_status_obj:
                    latest_status = {
                        'id': latest_status_obj.id,
                        'imei': latest_status_obj.imei,
                        'battery': latest_status_obj.battery,
                        'signal': latest_status_obj.signal,
                        'ignition': latest_status_obj.ignition,
                        'charging': latest_status_obj.charging,
                        'relay': latest_status_obj.relay,
                        'createdAt': latest_status_obj.createdAt.isoformat(),
                        'updatedAt': latest_status_obj.updatedAt.isoformat() if hasattr(latest_status_obj, 'updatedAt') and latest_status_obj.updatedAt else latest_status_obj.createdAt.isoformat()
                    }
            except Exception as e:
                latest_status = None
            
            devices_data.append({
                'id': device.id,
                'imei': device.imei,
                'phone': device.phone,
                'sim': device.sim,
                'protocol': device.protocol,
                'iccid': device.iccid,
                'model': device.model,
                'type': device.type,
                'status': 'active',  # Default status
                'subscription_plan': {
                    'id': device.subscription_plan.id,
                    'title': device.subscription_plan.title,
                    'price': float(device.subscription_plan.price)
                } if device.subscription_plan else None,
                'userDevices': user_devices_data,
                'vehicles': vehicles_data,
                'latestStatus': latest_status,
                'createdAt': device.createdAt.isoformat(),
                'updatedAt': device.updatedAt.isoformat()
            })
        
        # Prepare pagination info
        pagination_info = {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None
        }
        
        response_data = {
            'devices': devices_data,
            'pagination': pagination_info
        }
        
        return success_response(
            data=response_data,
            message='GPS devices retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_buzzer_devices_paginated(request):
    """
    Get paginated Buzzer devices with search functionality
    """
    try:
        from django.db.models import Q
        from django.core.paginator import Paginator
        
        user = request.user
        search_query = request.GET.get('q', '').strip()
        page_number = int(request.GET.get('page', 1))
        page_size = 25  # Fixed page size
        
        # Get user groups (Django's role system)
        user_groups = user.groups.all()
        is_super_admin = any(group.name == 'Super Admin' for group in user_groups)
        is_dealer = any(group.name == 'Dealer' for group in user_groups)
        
        # Super Admin: all Buzzer devices
        if is_super_admin:
            devices = Device.objects.filter(type='buzzer').prefetch_related(
                'userDevices__user__groups',
                'vehicles__userVehicles__user__groups',
                'subscription_plan'
            ).all()
        # Dealer: only assigned Buzzer devices
        elif is_dealer:
            devices = Device.objects.filter(
                type='buzzer',
                userDevices__user=user
            ).prefetch_related(
                'userDevices__user__groups',
                'vehicles__userVehicles__user__groups',
                'subscription_plan'
            ).distinct()
        # Customer: no access to devices
        else:
            return error_response(
                message='Access denied. Customers cannot view devices',
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        # Apply search filter if query provided
        if search_query:
            search_filter = Q()
            search_filter |= Q(imei__icontains=search_query)
            search_filter |= Q(phone__icontains=search_query)
            search_filter |= Q(protocol__icontains=search_query)
            search_filter |= Q(sim__icontains=search_query)
            search_filter |= Q(model__icontains=search_query)
            search_filter |= Q(iccid__icontains=search_query)
            search_filter |= Q(userDevices__user__name__icontains=search_query)
            search_filter |= Q(userDevices__user__phone__icontains=search_query)
            search_filter |= Q(vehicles__vehicleNo__icontains=search_query)
            search_filter |= Q(vehicles__name__icontains=search_query)
            search_filter |= Q(vehicles__userVehicles__user__name__icontains=search_query)
            search_filter |= Q(vehicles__userVehicles__user__phone__icontains=search_query)
            devices = devices.filter(search_filter).distinct()
        
        # Create paginator
        paginator = Paginator(devices, page_size)
        
        # Get the requested page
        try:
            page_obj = paginator.get_page(page_number)
        except:
            return error_response('Invalid page number', HTTP_STATUS['BAD_REQUEST'])
        
        devices_data = []
        for device in page_obj:
            # Get user devices with user info and roles
            user_devices_data = []
            for user_device in device.userDevices.all():
                user_data = {
                    'id': user_device.user.id,
                    'name': user_device.user.name,
                    'phone': user_device.user.phone,
                    'status': 'active',  # Default status
                    'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in user_device.user.groups.all()],
                    'createdAt': user_device.createdAt.isoformat(),
                    'updatedAt': user_device.createdAt.isoformat()
                }
                user_devices_data.append({
                    'id': user_device.id,
                    'userId': user_device.user.id,
                    'deviceId': device.id,
                    'user': user_data,
                    'createdAt': user_device.createdAt.isoformat(),
                    'updatedAt': user_device.createdAt.isoformat()
                })
            
            # Get vehicles with user vehicles
            vehicles_data = []
            for vehicle in device.vehicles.all():
                user_vehicles_data = []
                for user_vehicle in vehicle.userVehicles.all():
                    user_data = {
                        'id': user_vehicle.user.id,
                        'name': user_vehicle.user.name,
                        'phone': user_vehicle.user.phone,
                        'status': 'active',  # Default status
                        'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in user_vehicle.user.groups.all()],
                        'createdAt': user_vehicle.createdAt.isoformat(),
                        'updatedAt': user_vehicle.createdAt.isoformat()
                    }
                    user_vehicles_data.append({
                        'id': user_vehicle.id,
                        'userId': user_vehicle.user.id,
                        'vehicleId': vehicle.id,
                        'isMain': user_vehicle.isMain,
                        'user': user_data,
                        'relay': getattr(user_vehicle, 'relay', False),
                        'createdAt': user_vehicle.createdAt.isoformat(),
                        'updatedAt': user_vehicle.createdAt.isoformat()
                    })
                
                vehicles_data.append({
                    'id': vehicle.id,
                    'imei': vehicle.imei,
                    'name': vehicle.name,
                    'vehicleNo': vehicle.vehicleNo,
                    'vehicleType': vehicle.vehicleType,
                    'userVehicles': user_vehicles_data
                })
            
            # Get latest status for Buzzer device (BuzzerStatus table)
            latest_status = None
            try:
                latest_status_obj = BuzzerStatus.objects.filter(imei=device.imei).order_by('-createdAt', '-updatedAt').first()
                if latest_status_obj:
                    latest_status = {
                        'id': latest_status_obj.id,
                        'imei': latest_status_obj.imei,
                        'battery': latest_status_obj.battery,
                        'signal': latest_status_obj.signal,
                        'ignition': latest_status_obj.ignition,
                        'charging': latest_status_obj.charging,
                        'relay': latest_status_obj.relay,
                        'createdAt': latest_status_obj.createdAt.isoformat(),
                        'updatedAt': latest_status_obj.updatedAt.isoformat() if hasattr(latest_status_obj, 'updatedAt') and latest_status_obj.updatedAt else latest_status_obj.createdAt.isoformat()
                    }
            except Exception as e:
                latest_status = None
            
            devices_data.append({
                'id': device.id,
                'imei': device.imei,
                'phone': device.phone,
                'sim': device.sim,
                'protocol': device.protocol,
                'iccid': device.iccid,
                'model': device.model,
                'type': device.type,
                'status': 'active',  # Default status
                'subscription_plan': {
                    'id': device.subscription_plan.id,
                    'title': device.subscription_plan.title,
                    'price': float(device.subscription_plan.price)
                } if device.subscription_plan else None,
                'userDevices': user_devices_data,
                'vehicles': vehicles_data,
                'latestStatus': latest_status,
                'createdAt': device.createdAt.isoformat(),
                'updatedAt': device.updatedAt.isoformat()
            })
        
        # Prepare pagination info
        pagination_info = {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None
        }
        
        response_data = {
            'devices': devices_data,
            'pagination': pagination_info
        }
        
        return success_response(
            data=response_data,
            message='Buzzer devices retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_sos_devices_paginated(request):
    """
    Get paginated SOS devices with search functionality
    """
    try:
        from django.db.models import Q
        from django.core.paginator import Paginator
        
        user = request.user
        search_query = request.GET.get('q', '').strip()
        page_number = int(request.GET.get('page', 1))
        page_size = 25  # Fixed page size
        
        # Get user groups (Django's role system)
        user_groups = user.groups.all()
        is_super_admin = any(group.name == 'Super Admin' for group in user_groups)
        is_dealer = any(group.name == 'Dealer' for group in user_groups)
        
        # Super Admin: all SOS devices
        if is_super_admin:
            devices = Device.objects.filter(type='sos').prefetch_related(
                'userDevices__user__groups',
                'vehicles__userVehicles__user__groups',
                'subscription_plan'
            ).all()
        # Dealer: only assigned SOS devices
        elif is_dealer:
            devices = Device.objects.filter(
                type='sos',
                userDevices__user=user
            ).prefetch_related(
                'userDevices__user__groups',
                'vehicles__userVehicles__user__groups',
                'subscription_plan'
            ).distinct()
        # Customer: no access to devices
        else:
            return error_response(
                message='Access denied. Customers cannot view devices',
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        # Apply search filter if query provided
        if search_query:
            search_filter = Q()
            search_filter |= Q(imei__icontains=search_query)
            search_filter |= Q(phone__icontains=search_query)
            search_filter |= Q(protocol__icontains=search_query)
            search_filter |= Q(sim__icontains=search_query)
            search_filter |= Q(model__icontains=search_query)
            search_filter |= Q(iccid__icontains=search_query)
            search_filter |= Q(userDevices__user__name__icontains=search_query)
            search_filter |= Q(userDevices__user__phone__icontains=search_query)
            search_filter |= Q(vehicles__vehicleNo__icontains=search_query)
            search_filter |= Q(vehicles__name__icontains=search_query)
            search_filter |= Q(vehicles__userVehicles__user__name__icontains=search_query)
            search_filter |= Q(vehicles__userVehicles__user__phone__icontains=search_query)
            devices = devices.filter(search_filter).distinct()
        
        # Create paginator
        paginator = Paginator(devices, page_size)
        
        # Get the requested page
        try:
            page_obj = paginator.get_page(page_number)
        except:
            return error_response('Invalid page number', HTTP_STATUS['BAD_REQUEST'])
        
        devices_data = []
        for device in page_obj:
            # Get user devices with user info and roles
            user_devices_data = []
            for user_device in device.userDevices.all():
                user_data = {
                    'id': user_device.user.id,
                    'name': user_device.user.name,
                    'phone': user_device.user.phone,
                    'status': 'active',  # Default status
                    'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in user_device.user.groups.all()],
                    'createdAt': user_device.createdAt.isoformat(),
                    'updatedAt': user_device.createdAt.isoformat()
                }
                user_devices_data.append({
                    'id': user_device.id,
                    'userId': user_device.user.id,
                    'deviceId': device.id,
                    'user': user_data,
                    'createdAt': user_device.createdAt.isoformat(),
                    'updatedAt': user_device.createdAt.isoformat()
                })
            
            # Get vehicles with user vehicles
            vehicles_data = []
            for vehicle in device.vehicles.all():
                user_vehicles_data = []
                for user_vehicle in vehicle.userVehicles.all():
                    user_data = {
                        'id': user_vehicle.user.id,
                        'name': user_vehicle.user.name,
                        'phone': user_vehicle.user.phone,
                        'status': 'active',  # Default status
                        'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in user_vehicle.user.groups.all()],
                        'createdAt': user_vehicle.createdAt.isoformat(),
                        'updatedAt': user_vehicle.createdAt.isoformat()
                    }
                    user_vehicles_data.append({
                        'id': user_vehicle.id,
                        'userId': user_vehicle.user.id,
                        'vehicleId': vehicle.id,
                        'isMain': user_vehicle.isMain,
                        'user': user_data,
                        'relay': getattr(user_vehicle, 'relay', False),
                        'createdAt': user_vehicle.createdAt.isoformat(),
                        'updatedAt': user_vehicle.createdAt.isoformat()
                    })
                
                vehicles_data.append({
                    'id': vehicle.id,
                    'imei': vehicle.imei,
                    'name': vehicle.name,
                    'vehicleNo': vehicle.vehicleNo,
                    'vehicleType': vehicle.vehicleType,
                    'userVehicles': user_vehicles_data
                })
            
            # Get latest status for SOS device (SosStatus table)
            latest_status = None
            try:
                latest_status_obj = SosStatus.objects.filter(imei=device.imei).order_by('-createdAt', '-updatedAt').first()
                if latest_status_obj:
                    latest_status = {
                        'id': latest_status_obj.id,
                        'imei': latest_status_obj.imei,
                        'battery': latest_status_obj.battery,
                        'signal': latest_status_obj.signal,
                        'ignition': latest_status_obj.ignition,
                        'charging': latest_status_obj.charging,
                        'relay': latest_status_obj.relay,
                        'createdAt': latest_status_obj.createdAt.isoformat(),
                        'updatedAt': latest_status_obj.updatedAt.isoformat() if hasattr(latest_status_obj, 'updatedAt') and latest_status_obj.updatedAt else latest_status_obj.createdAt.isoformat()
                    }
            except Exception as e:
                latest_status = None
            
            devices_data.append({
                'id': device.id,
                'imei': device.imei,
                'phone': device.phone,
                'sim': device.sim,
                'protocol': device.protocol,
                'iccid': device.iccid,
                'model': device.model,
                'type': device.type,
                'status': 'active',  # Default status
                'subscription_plan': {
                    'id': device.subscription_plan.id,
                    'title': device.subscription_plan.title,
                    'price': float(device.subscription_plan.price)
                } if device.subscription_plan else None,
                'userDevices': user_devices_data,
                'vehicles': vehicles_data,
                'latestStatus': latest_status,
                'createdAt': device.createdAt.isoformat(),
                'updatedAt': device.updatedAt.isoformat()
            })
        
        # Prepare pagination info
        pagination_info = {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None
        }
        
        response_data = {
            'devices': devices_data,
            'pagination': pagination_info
        }
        
        return success_response(
            data=response_data,
            message='SOS devices retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )