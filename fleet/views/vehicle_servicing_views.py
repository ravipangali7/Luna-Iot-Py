"""
Vehicle Servicing Views
Handles CRUD operations for vehicle servicing records
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from datetime import datetime, timedelta

from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.auth_decorators import require_auth
from api_common.constants.api_constants import HTTP_STATUS
from api_common.utils.exception_utils import handle_api_exception

from fleet.models import Vehicle, VehicleServicing, UserVehicle
from fleet.serializers.vehicle_servicing_serializers import (
    VehicleServicingSerializer,
    VehicleServicingCreateSerializer,
    VehicleServicingUpdateSerializer,
    VehicleServicingListSerializer
)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_vehicle_servicings(request, imei):
    """Get all servicing records for a vehicle"""
    try:
        user = request.user
        
        # Get vehicle and check access
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check user access to vehicle
        user_group = user.groups.first()
        has_access = False
        if user_group and user_group.name == 'Super Admin':
            has_access = True
        else:
            has_access = vehicle.userVehicles.filter(user=user).exists() or \
                        vehicle.device.userDevices.filter(user=user).exists()
        
        if not has_access:
            return error_response('Access denied', HTTP_STATUS['FORBIDDEN'])
        
        servicings = VehicleServicing.objects.filter(vehicle=vehicle).order_by('-date', '-created_at')
        serializer = VehicleServicingListSerializer(servicings, many=True)
        
        return success_response(serializer.data, 'Servicing records retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def create_vehicle_servicing(request, imei):
    """Create a new servicing record for a vehicle"""
    try:
        user = request.user
        
        # Get vehicle and check access
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check user access to vehicle
        user_group = user.groups.first()
        has_access = False
        if user_group and user_group.name == 'Super Admin':
            has_access = True
        else:
            user_vehicle = vehicle.userVehicles.filter(user=user).first()
            has_access = user_vehicle and (user_vehicle.allAccess or user_vehicle.edit)
        
        if not has_access:
            return error_response('Access denied', HTTP_STATUS['FORBIDDEN'])
        
        # Parse request data
        import json
        data = json.loads(request.body) if request.body else {}
        data['vehicle'] = vehicle.id
        
        serializer = VehicleServicingCreateSerializer(data=data)
        if serializer.is_valid():
            servicing = serializer.save()
            response_serializer = VehicleServicingSerializer(servicing)
            return success_response(response_serializer.data, 'Servicing record created successfully')
        else:
            return error_response(serializer.errors, HTTP_STATUS['BAD_REQUEST'])
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["PUT"])
@require_auth
def update_vehicle_servicing(request, imei, servicing_id):
    """Update a servicing record"""
    try:
        user = request.user
        
        # Get vehicle and check access
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Get servicing record
        try:
            servicing = VehicleServicing.objects.get(id=servicing_id, vehicle=vehicle)
        except VehicleServicing.DoesNotExist:
            return error_response('Servicing record not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check user access
        user_group = user.groups.first()
        has_access = False
        if user_group and user_group.name == 'Super Admin':
            has_access = True
        else:
            user_vehicle = vehicle.userVehicles.filter(user=user).first()
            has_access = user_vehicle and (user_vehicle.allAccess or user_vehicle.edit)
        
        if not has_access:
            return error_response('Access denied', HTTP_STATUS['FORBIDDEN'])
        
        # Parse request data
        import json
        data = json.loads(request.body) if request.body else {}
        
        serializer = VehicleServicingUpdateSerializer(servicing, data=data, partial=True)
        if serializer.is_valid():
            servicing = serializer.save()
            response_serializer = VehicleServicingSerializer(servicing)
            return success_response(response_serializer.data, 'Servicing record updated successfully')
        else:
            return error_response(serializer.errors, HTTP_STATUS['BAD_REQUEST'])
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["DELETE"])
@require_auth
def delete_vehicle_servicing(request, imei, servicing_id):
    """Delete a servicing record"""
    try:
        user = request.user
        
        # Get vehicle and check access
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Get servicing record
        try:
            servicing = VehicleServicing.objects.get(id=servicing_id, vehicle=vehicle)
        except VehicleServicing.DoesNotExist:
            return error_response('Servicing record not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check user access
        user_group = user.groups.first()
        has_access = False
        if user_group and user_group.name == 'Super Admin':
            has_access = True
        else:
            user_vehicle = vehicle.userVehicles.filter(user=user).first()
            has_access = user_vehicle and (user_vehicle.allAccess or user_vehicle.edit)
        
        if not has_access:
            return error_response('Access denied', HTTP_STATUS['FORBIDDEN'])
        
        servicing.delete()
        return success_response(None, 'Servicing record deleted successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def check_servicing_threshold(request, imei):
    """Check if vehicle needs servicing based on 25% threshold"""
    try:
        user = request.user
        
        # Get vehicle and check access
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check user access to vehicle
        user_group = user.groups.first()
        has_access = False
        if user_group and user_group.name == 'Super Admin':
            has_access = True
        else:
            has_access = vehicle.userVehicles.filter(user=user).exists() or \
                        vehicle.device.userDevices.filter(user=user).exists()
        
        if not has_access:
            return error_response('Access denied', HTTP_STATUS['FORBIDDEN'])
        
        # Get last servicing record
        last_servicing = VehicleServicing.objects.filter(vehicle=vehicle).order_by('-date', '-odometer').first()
        
        if not last_servicing:
            # No previous servicing, check if current odometer >= 75% of period
            threshold_odometer = vehicle.servicing_distance_period * 0.75
            needs_servicing = float(vehicle.odometer) >= threshold_odometer
            return success_response({
                'needs_servicing': needs_servicing,
                'current_odometer': float(vehicle.odometer),
                'threshold_odometer': threshold_odometer,
                'last_service_odometer': None,
                'last_service_date': None
            }, 'Threshold check completed')
        
        # Calculate threshold: last_service_odometer + (servicing_distance_period * 0.75)
        threshold_odometer = float(last_servicing.odometer) + (vehicle.servicing_distance_period * 0.75)
        current_odometer = float(vehicle.odometer)
        needs_servicing = current_odometer >= threshold_odometer
        
        return success_response({
            'needs_servicing': needs_servicing,
            'current_odometer': current_odometer,
            'threshold_odometer': threshold_odometer,
            'last_service_odometer': float(last_servicing.odometer),
            'last_service_date': last_servicing.date.isoformat() if last_servicing.date else None
        }, 'Threshold check completed')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_all_owned_vehicle_servicings(request):
    """Get all servicing records for all vehicles where user has isMain=True"""
    try:
        user = request.user
        
        # Get all vehicles where user has isMain=True
        user_group = user.groups.first()
        if user_group and user_group.name == 'Super Admin':
            # Super Admin can see all vehicles
            owned_vehicles = Vehicle.objects.all()
        else:
            # Get vehicles where user has isMain=True
            owned_vehicle_ids = UserVehicle.objects.filter(
                user=user,
                isMain=True
            ).values_list('vehicle_id', flat=True)
            owned_vehicles = Vehicle.objects.filter(id__in=owned_vehicle_ids)
        
        # Group servicings by vehicle
        result = {}
        for vehicle in owned_vehicles:
            servicings = VehicleServicing.objects.filter(vehicle=vehicle).order_by('-date', '-created_at')
            if servicings.exists():
                serializer = VehicleServicingListSerializer(servicings, many=True)
                result[str(vehicle.id)] = {
                    'vehicle_id': vehicle.id,
                    'vehicle_name': vehicle.name,
                    'vehicle_imei': vehicle.imei,
                    'servicings': serializer.data
                }
        
        return success_response(result, 'All owned vehicle servicing records retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)

