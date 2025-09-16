from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q
import json
import re

from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.auth_decorators import require_auth, require_role
from api_common.constants.api_constants import HTTP_STATUS_CODES
from api_common.utils.validation_utils import validate_required_fields, validate_imei
from api_common.utils.exception_utils import handle_exception

from fleet.models import Vehicle, UserVehicle
from device.models import Device
from core.models import User


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_all_vehicles(request):
    """
    Get all vehicles with complete data (ownership, today's km, latest status and location)
    """
    try:
        user = request.user
        
        # Get vehicles based on user role
        if user.role.name == 'Super Admin':
            vehicles = Vehicle.objects.select_related('device').prefetch_related('uservehicle_set__user').all()
        else:
            # Get vehicles where user has access
            vehicles = Vehicle.objects.filter(
                uservehicle__user=user
            ).select_related('device').prefetch_related('uservehicle_set__user').distinct()
        
        vehicles_data = []
        for vehicle in vehicles:
            # Get user vehicle relationship
            user_vehicle = vehicle.uservehicle_set.filter(user=user).first()
            
            # Get today's km (you'll need to implement this based on your location model)
            today_km = 0  # Placeholder - implement based on location data
            
            # Get latest status and location (you'll need to implement these)
            latest_status = None  # Placeholder - implement based on status model
            latest_location = None  # Placeholder - implement based on location model
            
            vehicle_data = {
                'id': vehicle.id,
                'imei': vehicle.imei,
                'name': vehicle.name,
                'vehicleNo': vehicle.vehicle_no,
                'vehicleType': vehicle.vehicle_type,
                'status': vehicle.status,
                'createdAt': vehicle.created_at.isoformat() if vehicle.created_at else None,
                'updatedAt': vehicle.updated_at.isoformat() if vehicle.updated_at else None,
                'userVehicle': {
                    'isMain': user_vehicle.is_main if user_vehicle else False,
                    'permissions': user_vehicle.permissions if user_vehicle else []
                } if user_vehicle else None,
                'todayKm': today_km,
                'latestStatus': latest_status,
                'latestLocation': latest_location
            }
            vehicles_data.append(vehicle_data)
        
        return success_response(vehicles_data, 'Vehicles retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve vehicles')


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_all_vehicles_detailed(request):
    """
    Get all vehicles with detailed data for table display (includes device, user, recharge info)
    """
    try:
        user = request.user
        
        # Get vehicles based on user role
        if user.role.name == 'Super Admin':
            vehicles = Vehicle.objects.select_related('device').prefetch_related('uservehicle_set__user').all()
        else:
            # Get vehicles where user has access
            vehicles = Vehicle.objects.filter(
                uservehicle__user=user
            ).select_related('device').prefetch_related('uservehicle_set__user').distinct()
        
        vehicles_data = []
        for vehicle in vehicles:
            # Get all users with access to this vehicle
            users_with_access = []
            for uv in vehicle.uservehicle_set.all():
                users_with_access.append({
                    'id': uv.user.id,
                    'name': uv.user.name,
                    'phone': uv.user.phone,
                    'isMain': uv.is_main,
                    'permissions': uv.permissions
                })
            
            # Get recharge info (you'll need to implement this based on your recharge model)
            recharge_info = None  # Placeholder - implement based on recharge model
            
            vehicle_data = {
                'id': vehicle.id,
                'imei': vehicle.imei,
                'name': vehicle.name,
                'vehicleNo': vehicle.vehicle_no,
                'vehicleType': vehicle.vehicle_type,
                'status': vehicle.status,
                'createdAt': vehicle.created_at.isoformat() if vehicle.created_at else None,
                'updatedAt': vehicle.updated_at.isoformat() if vehicle.updated_at else None,
                'device': {
                    'id': vehicle.device.id,
                    'imei': vehicle.device.imei,
                    'name': vehicle.device.name,
                    'status': vehicle.device.status
                } if vehicle.device else None,
                'users': users_with_access,
                'rechargeInfo': recharge_info
            }
            vehicles_data.append(vehicle_data)
        
        return success_response(vehicles_data, 'Detailed vehicles retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve detailed vehicles')


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_vehicle_by_imei(request, imei):
    """
    Get vehicle by IMEI with complete data and role-based access
    """
    try:
        user = request.user
        
        # Get vehicle with access check
        if user.role.name == 'Super Admin':
            vehicle = Vehicle.objects.select_related('device').prefetch_related('uservehicle_set__user').filter(imei=imei).first()
        else:
            vehicle = Vehicle.objects.filter(
                imei=imei,
                uservehicle__user=user
            ).select_related('device').prefetch_related('uservehicle_set__user').first()
        
        if not vehicle:
            return error_response('Vehicle not found or access denied', HTTP_STATUS_CODES['NOT_FOUND'])
        
        # Get user vehicle relationship
        user_vehicle = vehicle.uservehicle_set.filter(user=user).first()
        
        # Get today's km (you'll need to implement this based on your location model)
        today_km = 0  # Placeholder - implement based on location data
        
        # Get latest status and location (you'll need to implement these)
        latest_status = None  # Placeholder - implement based on status model
        latest_location = None  # Placeholder - implement based on location model
        
        # Get all users with access to this vehicle
        users_with_access = []
        for uv in vehicle.uservehicle_set.all():
            users_with_access.append({
                'id': uv.user.id,
                'name': uv.user.name,
                'phone': uv.user.phone,
                'isMain': uv.is_main,
                'permissions': uv.permissions
            })
        
        vehicle_data = {
            'id': vehicle.id,
            'imei': vehicle.imei,
            'name': vehicle.name,
            'vehicleNo': vehicle.vehicle_no,
            'vehicleType': vehicle.vehicle_type,
            'status': vehicle.status,
            'createdAt': vehicle.created_at.isoformat() if vehicle.created_at else None,
            'updatedAt': vehicle.updated_at.isoformat() if vehicle.updated_at else None,
            'device': {
                'id': vehicle.device.id,
                'imei': vehicle.device.imei,
                'name': vehicle.device.name,
                'status': vehicle.device.status
            } if vehicle.device else None,
            'userVehicle': {
                'isMain': user_vehicle.is_main if user_vehicle else False,
                'permissions': user_vehicle.permissions if user_vehicle else []
            } if user_vehicle else None,
            'users': users_with_access,
            'todayKm': today_km,
            'latestStatus': latest_status,
            'latestLocation': latest_location
        }
        
        return success_response(vehicle_data, 'Vehicle retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve vehicle')


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def create_vehicle(request):
    """
    Create new vehicle with user-vehicle relationship
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['imei', 'name', 'vehicleNo', 'vehicleType']
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return validation_error
        
        # Validate IMEI format
        if not validate_imei(data['imei']):
            return error_response('IMEI must be exactly 15 digits', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Check if device IMEI exists
        try:
            device = Device.objects.get(imei=data['imei'])
        except Device.DoesNotExist:
            return error_response('Device with this IMEI does not exist. Please create the device first.', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Check if vehicle with this IMEI already exists
        if Vehicle.objects.filter(imei=data['imei']).exists():
            return error_response('Vehicle with this IMEI already exists', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Create vehicle
        with transaction.atomic():
            vehicle = Vehicle.objects.create(
                imei=data['imei'],
                name=data['name'],
                vehicle_no=data['vehicleNo'],
                vehicle_type=data['vehicleType'],
                device=device,
                status=data.get('status', 'ACTIVE')
            )
            
            # Create user-vehicle relationship
            UserVehicle.objects.create(
                vehicle=vehicle,
                user=user,
                is_main=True,
                permissions=data.get('permissions', [])
            )
        
        vehicle_data = {
            'id': vehicle.id,
            'imei': vehicle.imei,
            'name': vehicle.name,
            'vehicleNo': vehicle.vehicle_no,
            'vehicleType': vehicle.vehicle_type,
            'status': vehicle.status,
            'createdAt': vehicle.created_at.isoformat() if vehicle.created_at else None,
            'updatedAt': vehicle.updated_at.isoformat() if vehicle.updated_at else None
        }
        
        return success_response(vehicle_data, 'Vehicle created successfully', HTTP_STATUS_CODES['CREATED'])
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS_CODES['BAD_REQUEST'])
    except Exception as e:
        return handle_exception(e, 'Failed to create vehicle')


@csrf_exempt
@require_http_methods(["PUT"])
@require_auth
def update_vehicle(request, imei):
    """
    Update vehicle with role-based access
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        # Get vehicle with access check
        if user.role.name == 'Super Admin':
            vehicle = Vehicle.objects.select_related('device').filter(imei=imei).first()
        else:
            vehicle = Vehicle.objects.filter(
                imei=imei,
                uservehicle__user=user
            ).select_related('device').first()
        
        if not vehicle:
            return error_response('Vehicle not found or access denied', HTTP_STATUS_CODES['NOT_FOUND'])
        
        # Only check for device existence and vehicle duplicates if IMEI is being changed
        if 'imei' in data and data['imei'] != imei:
            # Check if device exists
            try:
                device = Device.objects.get(imei=data['imei'])
            except Device.DoesNotExist:
                return error_response('Device with this IMEI does not exist', HTTP_STATUS_CODES['BAD_REQUEST'])
            
            # Check if another vehicle with the new IMEI already exists
            if Vehicle.objects.filter(imei=data['imei']).exclude(id=vehicle.id).exists():
                return error_response('Vehicle with this IMEI already exists', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Update vehicle
        with transaction.atomic():
            if 'imei' in data:
                vehicle.imei = data['imei']
            if 'name' in data:
                vehicle.name = data['name']
            if 'vehicleNo' in data:
                vehicle.vehicle_no = data['vehicleNo']
            if 'vehicleType' in data:
                vehicle.vehicle_type = data['vehicleType']
            if 'status' in data:
                vehicle.status = data['status']
            
            vehicle.save()
        
        vehicle_data = {
            'id': vehicle.id,
            'imei': vehicle.imei,
            'name': vehicle.name,
            'vehicleNo': vehicle.vehicle_no,
            'vehicleType': vehicle.vehicle_type,
            'status': vehicle.status,
            'createdAt': vehicle.created_at.isoformat() if vehicle.created_at else None,
            'updatedAt': vehicle.updated_at.isoformat() if vehicle.updated_at else None
        }
        
        return success_response(vehicle_data, 'Vehicle updated successfully')
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS_CODES['BAD_REQUEST'])
    except Exception as e:
        return handle_exception(e, 'Failed to update vehicle')


@csrf_exempt
@require_http_methods(["DELETE"])
@require_auth
@require_role(['Super Admin'])
def delete_vehicle(request, imei):
    """
    Delete vehicle (only Super Admin)
    """
    try:
        # Get vehicle
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS_CODES['NOT_FOUND'])
        
        # Delete vehicle and related data
        with transaction.atomic():
            # Delete user-vehicle relationships
            UserVehicle.objects.filter(vehicle=vehicle).delete()
            
            # Delete geofence-vehicle relationships (you'll need to implement this)
            # GeofenceVehicle.objects.filter(vehicle=vehicle).delete()
            
            # Delete ALL location data with this IMEI (you'll need to implement this)
            # Location.objects.filter(imei=imei).delete()
            
            # Delete ALL status data with this IMEI (you'll need to implement this)
            # Status.objects.filter(imei=imei).delete()
            
            # Delete the vehicle record itself
            vehicle.delete()
        
        return success_response(None, 'Vehicle deleted successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to delete vehicle')


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def assign_vehicle_access_to_user(request):
    """
    Assign vehicle access to user
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['imei', 'userPhone', 'permissions']
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return validation_error
        
        imei = data['imei']
        user_phone = data['userPhone']
        permissions = data['permissions']
        
        # Check if target user exists
        try:
            target_user = User.objects.get(phone=user_phone)
        except User.DoesNotExist:
            return error_response('User not found', HTTP_STATUS_CODES['NOT_FOUND'])
        
        # Check if user has permission to assign access
        if user.role.name != 'Super Admin':
            try:
                main_user_vehicle = UserVehicle.objects.get(
                    vehicle__imei=imei,
                    user=user,
                    is_main=True
                )
            except UserVehicle.DoesNotExist:
                return error_response('Access denied. Only main user or Super Admin can assign access', HTTP_STATUS_CODES['FORBIDDEN'])
        
        # Check if vehicle exists
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS_CODES['NOT_FOUND'])
        
        # Check if access is already assigned
        if UserVehicle.objects.filter(vehicle=vehicle, user=target_user).exists():
            return error_response('Vehicle access is already assigned to this user', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Assign vehicle access to user
        user_vehicle = UserVehicle.objects.create(
            vehicle=vehicle,
            user=target_user,
            is_main=False,
            permissions=permissions
        )
        
        assignment_data = {
            'id': user_vehicle.id,
            'vehicleId': vehicle.id,
            'userId': target_user.id,
            'isMain': user_vehicle.is_main,
            'permissions': user_vehicle.permissions,
            'createdAt': user_vehicle.created_at.isoformat() if user_vehicle.created_at else None
        }
        
        return success_response(assignment_data, 'Vehicle access assigned successfully')
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS_CODES['BAD_REQUEST'])
    except Exception as e:
        return handle_exception(e, 'Failed to assign vehicle access')


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_vehicles_for_access_assignment(request):
    """
    Get vehicles for access assignment
    """
    try:
        user = request.user
        
        # Get vehicles based on user role
        if user.role.name == 'Super Admin':
            vehicles = Vehicle.objects.all()
        else:
            # Get vehicles where user is main user
            vehicles = Vehicle.objects.filter(
                uservehicle__user=user,
                uservehicle__is_main=True
            ).distinct()
        
        vehicles_data = []
        for vehicle in vehicles:
            vehicles_data.append({
                'id': vehicle.id,
                'imei': vehicle.imei,
                'name': vehicle.name,
                'vehicleNo': vehicle.vehicle_no,
                'vehicleType': vehicle.vehicle_type
            })
        
        return success_response(vehicles_data, 'Vehicles for access assignment retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve vehicles for access assignment')


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_vehicle_access_assignments(request, imei):
    """
    Get vehicle access assignments
    """
    try:
        user = request.user
        
        if not imei:
            return error_response('IMEI is required', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Check if user has access to this vehicle
        if user.role.name != 'Super Admin':
            try:
                UserVehicle.objects.get(
                    vehicle__imei=imei,
                    user=user,
                    is_main=True
                )
            except UserVehicle.DoesNotExist:
                return error_response('Access denied', HTTP_STATUS_CODES['FORBIDDEN'])
        
        # Get vehicle access assignments
        user_vehicles = UserVehicle.objects.filter(
            vehicle__imei=imei
        ).select_related('user')
        
        assignments_data = []
        for uv in user_vehicles:
            assignments_data.append({
                'id': uv.id,
                'userId': uv.user.id,
                'userName': uv.user.name,
                'userPhone': uv.user.phone,
                'isMain': uv.is_main,
                'permissions': uv.permissions,
                'createdAt': uv.created_at.isoformat() if uv.created_at else None
            })
        
        return success_response(assignments_data, 'Vehicle access assignments retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve vehicle access assignments')


@csrf_exempt
@require_http_methods(["PUT"])
@require_auth
def update_vehicle_access(request):
    """
    Update vehicle access
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['imei', 'userId', 'permissions']
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return validation_error
        
        imei = data['imei']
        user_id = data['userId']
        permissions = data['permissions']
        
        # Check if user has permission to update access
        if user.role.name != 'Super Admin':
            try:
                main_user_vehicle = UserVehicle.objects.get(
                    vehicle__imei=imei,
                    user=user,
                    is_main=True
                )
            except UserVehicle.DoesNotExist:
                return error_response('Access denied. Only main user or Super Admin can update access', HTTP_STATUS_CODES['FORBIDDEN'])
        
        # Check if vehicle exists
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS_CODES['NOT_FOUND'])
        
        # Update vehicle access
        try:
            user_vehicle = UserVehicle.objects.get(vehicle=vehicle, user_id=user_id)
            user_vehicle.permissions = permissions
            user_vehicle.save()
        except UserVehicle.DoesNotExist:
            return error_response('Vehicle access assignment not found', HTTP_STATUS_CODES['NOT_FOUND'])
        
        assignment_data = {
            'id': user_vehicle.id,
            'vehicleId': vehicle.id,
            'userId': user_vehicle.user.id,
            'isMain': user_vehicle.is_main,
            'permissions': user_vehicle.permissions,
            'createdAt': user_vehicle.created_at.isoformat() if user_vehicle.created_at else None
        }
        
        return success_response(assignment_data, 'Vehicle access updated successfully')
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS_CODES['BAD_REQUEST'])
    except Exception as e:
        return handle_exception(e, 'Failed to update vehicle access')


@csrf_exempt
@require_http_methods(["DELETE"])
@require_auth
def remove_vehicle_access(request):
    """
    Remove vehicle access
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['imei', 'userId']
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return validation_error
        
        imei = data['imei']
        user_id = data['userId']
        
        # Check if user has permission to remove access
        if user.role.name != 'Super Admin':
            try:
                main_user_vehicle = UserVehicle.objects.get(
                    vehicle__imei=imei,
                    user=user,
                    is_main=True
                )
            except UserVehicle.DoesNotExist:
                return error_response('Access denied. Only main user or Super Admin can remove access', HTTP_STATUS_CODES['FORBIDDEN'])
        
        # Check if vehicle exists
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS_CODES['NOT_FOUND'])
        
        # Remove vehicle access
        try:
            user_vehicle = UserVehicle.objects.get(vehicle=vehicle, user_id=user_id)
            user_vehicle.delete()
        except UserVehicle.DoesNotExist:
            return error_response('Vehicle access assignment not found', HTTP_STATUS_CODES['NOT_FOUND'])
        
        return success_response(None, 'Vehicle access removed successfully')
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS_CODES['BAD_REQUEST'])
    except Exception as e:
        return handle_exception(e, 'Failed to remove vehicle access')