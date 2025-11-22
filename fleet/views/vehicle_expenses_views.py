"""
Vehicle Expenses Views
Handles CRUD operations for vehicle expenses records
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.auth_decorators import require_auth
from api_common.constants.api_constants import HTTP_STATUS
from api_common.utils.exception_utils import handle_api_exception

from fleet.models import Vehicle, VehicleExpenses, UserVehicle
from fleet.serializers.vehicle_expenses_serializers import (
    VehicleExpensesSerializer,
    VehicleExpensesCreateSerializer,
    VehicleExpensesUpdateSerializer,
    VehicleExpensesListSerializer
)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_vehicle_expenses(request, imei):
    """Get all expenses records for a vehicle"""
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
        
        expenses = VehicleExpenses.objects.filter(vehicle=vehicle).order_by('-entry_date', '-created_at')
        serializer = VehicleExpensesListSerializer(expenses, many=True)
        
        return success_response(serializer.data, 'Expenses records retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def create_vehicle_expense(request, imei):
    """Create a new expense record for a vehicle"""
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
        
        serializer = VehicleExpensesCreateSerializer(data=data)
        if serializer.is_valid():
            expense = serializer.save()
            response_serializer = VehicleExpensesSerializer(expense)
            return success_response(response_serializer.data, 'Expense record created successfully')
        else:
            return error_response(serializer.errors, HTTP_STATUS['BAD_REQUEST'])
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["PUT"])
@require_auth
def update_vehicle_expense(request, imei, expense_id):
    """Update an expense record"""
    try:
        user = request.user
        
        # Get vehicle and check access
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Get expense record
        try:
            expense = VehicleExpenses.objects.get(id=expense_id, vehicle=vehicle)
        except VehicleExpenses.DoesNotExist:
            return error_response('Expense record not found', HTTP_STATUS['NOT_FOUND'])
        
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
        
        serializer = VehicleExpensesUpdateSerializer(expense, data=data, partial=True)
        if serializer.is_valid():
            expense = serializer.save()
            response_serializer = VehicleExpensesSerializer(expense)
            return success_response(response_serializer.data, 'Expense record updated successfully')
        else:
            return error_response(serializer.errors, HTTP_STATUS['BAD_REQUEST'])
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["DELETE"])
@require_auth
def delete_vehicle_expense(request, imei, expense_id):
    """Delete an expense record"""
    try:
        user = request.user
        
        # Get vehicle and check access
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Get expense record
        try:
            expense = VehicleExpenses.objects.get(id=expense_id, vehicle=vehicle)
        except VehicleExpenses.DoesNotExist:
            return error_response('Expense record not found', HTTP_STATUS['NOT_FOUND'])
        
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
        
        expense.delete()
        return success_response(None, 'Expense record deleted successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_all_owned_vehicle_expenses(request):
    """Get all expenses records for all vehicles where user has isMain=True"""
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
        
        # Group expenses by vehicle
        result = {}
        for vehicle in owned_vehicles:
            expenses = VehicleExpenses.objects.filter(vehicle=vehicle).order_by('-entry_date', '-created_at')
            if expenses.exists():
                serializer = VehicleExpensesListSerializer(expenses, many=True)
                result[str(vehicle.id)] = {
                    'vehicle_id': vehicle.id,
                    'vehicle_name': vehicle.name,
                    'vehicle_imei': vehicle.imei,
                    'expenses': serializer.data
                }
        
        return success_response(result, 'All owned vehicle expenses records retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)

