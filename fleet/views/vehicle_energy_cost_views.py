"""
Vehicle Energy Cost Views
Handles CRUD operations for vehicle energy cost records
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum

from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.auth_decorators import require_auth
from api_common.constants.api_constants import HTTP_STATUS
from api_common.utils.exception_utils import handle_api_exception

from fleet.models import Vehicle, VehicleEnergyCost
from fleet.serializers.vehicle_energy_cost_serializers import (
    VehicleEnergyCostSerializer,
    VehicleEnergyCostCreateSerializer,
    VehicleEnergyCostUpdateSerializer,
    VehicleEnergyCostListSerializer
)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_vehicle_energy_costs(request, imei):
    """Get all energy cost records for a vehicle"""
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
        
        energy_costs = VehicleEnergyCost.objects.filter(vehicle=vehicle).order_by('-entry_date', '-created_at')
        serializer = VehicleEnergyCostListSerializer(energy_costs, many=True)
        
        return success_response(serializer.data, 'Energy cost records retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def create_vehicle_energy_cost(request, imei):
    """Create a new energy cost record for a vehicle"""
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
        
        serializer = VehicleEnergyCostCreateSerializer(data=data)
        if serializer.is_valid():
            energy_cost = serializer.save()
            response_serializer = VehicleEnergyCostSerializer(energy_cost)
            return success_response(response_serializer.data, 'Energy cost record created successfully')
        else:
            return error_response(serializer.errors, HTTP_STATUS['BAD_REQUEST'])
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["PUT"])
@require_auth
def update_vehicle_energy_cost(request, imei, energy_cost_id):
    """Update an energy cost record"""
    try:
        user = request.user
        
        # Get vehicle and check access
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Get energy cost record
        try:
            energy_cost = VehicleEnergyCost.objects.get(id=energy_cost_id, vehicle=vehicle)
        except VehicleEnergyCost.DoesNotExist:
            return error_response('Energy cost record not found', HTTP_STATUS['NOT_FOUND'])
        
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
        
        serializer = VehicleEnergyCostUpdateSerializer(energy_cost, data=data, partial=True)
        if serializer.is_valid():
            energy_cost = serializer.save()
            response_serializer = VehicleEnergyCostSerializer(energy_cost)
            return success_response(response_serializer.data, 'Energy cost record updated successfully')
        else:
            return error_response(serializer.errors, HTTP_STATUS['BAD_REQUEST'])
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["DELETE"])
@require_auth
def delete_vehicle_energy_cost(request, imei, energy_cost_id):
    """Delete an energy cost record"""
    try:
        user = request.user
        
        # Get vehicle and check access
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Get energy cost record
        try:
            energy_cost = VehicleEnergyCost.objects.get(id=energy_cost_id, vehicle=vehicle)
        except VehicleEnergyCost.DoesNotExist:
            return error_response('Energy cost record not found', HTTP_STATUS['NOT_FOUND'])
        
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
        
        energy_cost.delete()
        return success_response(None, 'Energy cost record deleted successfully')
    
    except Exception as e:
        return handle_api_exception(e)

