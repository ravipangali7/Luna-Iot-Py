"""
Fleet Report Views
Handles report generation for vehicle fleet management
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count
from datetime import datetime, timedelta

from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.auth_decorators import require_auth
from api_common.constants.api_constants import HTTP_STATUS
from api_common.utils.exception_utils import handle_api_exception

from fleet.models import Vehicle, VehicleServicing, VehicleExpenses, VehicleEnergyCost
from fleet.serializers.fleet_report_serializers import FleetReportRequestSerializer
from fleet.serializers.vehicle_servicing_serializers import VehicleServicingListSerializer
from fleet.serializers.vehicle_expenses_serializers import VehicleExpensesListSerializer
from fleet.serializers.vehicle_energy_cost_serializers import VehicleEnergyCostListSerializer


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_vehicle_fleet_report(request, imei):
    """Get fleet report for a vehicle within date range"""
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
        
        # Get date range from query parameters
        from_date_str = request.GET.get('from_date')
        to_date_str = request.GET.get('to_date')
        
        if not from_date_str or not to_date_str:
            return error_response('from_date and to_date are required', HTTP_STATUS['BAD_REQUEST'])
        
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except ValueError:
            return error_response('Invalid date format. Use YYYY-MM-DD', HTTP_STATUS['BAD_REQUEST'])
        
        if from_date > to_date:
            return error_response('from_date cannot be greater than to_date', HTTP_STATUS['BAD_REQUEST'])
        
        # Calculate total days
        total_days = (to_date - from_date).days + 1
        
        # Get servicing records
        servicings = VehicleServicing.objects.filter(
            vehicle=vehicle,
            date__gte=from_date,
            date__lte=to_date
        ).order_by('-date')
        
        servicing_total_count = servicings.count()
        servicing_total_amount = servicings.aggregate(total=Sum('amount'))['total'] or 0
        servicing_details = VehicleServicingListSerializer(servicings, many=True).data
        
        # Get expenses records
        expenses = VehicleExpenses.objects.filter(
            vehicle=vehicle,
            entry_date__gte=from_date,
            entry_date__lte=to_date
        ).order_by('-entry_date')
        
        expenses_total_count = expenses.count()
        expenses_total_amount = expenses.aggregate(total=Sum('amount'))['total'] or 0
        
        # Expenses by type
        expenses_by_type = {}
        for expense_type in ['part', 'fine']:
            type_expenses = expenses.filter(expenses_type=expense_type)
            expenses_by_type[expense_type] = float(type_expenses.aggregate(total=Sum('amount'))['total'] or 0)
        
        expenses_details = VehicleExpensesListSerializer(expenses, many=True).data
        
        # Get energy cost records
        energy_costs = VehicleEnergyCost.objects.filter(
            vehicle=vehicle,
            entry_date__gte=from_date,
            entry_date__lte=to_date
        ).order_by('-entry_date')
        
        energy_cost_total_count = energy_costs.count()
        energy_cost_total_amount = energy_costs.aggregate(total=Sum('amount'))['total'] or 0
        energy_cost_total_units = energy_costs.aggregate(total=Sum('total_unit'))['total'] or 0
        
        # Energy cost by type
        energy_cost_by_type = {}
        for energy_type in ['fuel', 'electric']:
            type_costs = energy_costs.filter(energy_type=energy_type)
            energy_cost_by_type[energy_type] = float(type_costs.aggregate(total=Sum('amount'))['total'] or 0)
        
        energy_cost_details = VehicleEnergyCostListSerializer(energy_costs, many=True).data
        
        # Build report response
        report_data = {
            'total_days': total_days,
            'servicing': {
                'total_count': servicing_total_count,
                'total_amount': float(servicing_total_amount),
                'details': servicing_details
            },
            'expenses': {
                'total_count': expenses_total_count,
                'total_amount': float(expenses_total_amount),
                'by_type': expenses_by_type,
                'details': expenses_details
            },
            'energy_cost': {
                'total_count': energy_cost_total_count,
                'total_amount': float(energy_cost_total_amount),
                'total_units': float(energy_cost_total_units),
                'by_type': energy_cost_by_type,
                'details': energy_cost_details
            }
        }
        
        return success_response(report_data, 'Fleet report generated successfully')
    
    except Exception as e:
        return handle_api_exception(e)

