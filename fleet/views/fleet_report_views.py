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

from fleet.models import Vehicle, VehicleServicing, VehicleExpenses, VehicleEnergyCost, UserVehicle
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


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_all_vehicles_fleet_report(request):
    """Get fleet report for all vehicles user has access to within date range"""
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
        
        # Initialize aggregated totals
        total_servicing_count = 0
        total_servicing_amount = 0.0
        total_expenses_count = 0
        total_expenses_amount = 0.0
        total_energy_cost_count = 0
        total_energy_cost_amount = 0.0
        total_energy_cost_units = 0.0
        
        # Aggregated by type
        aggregated_expenses_by_type = {}
        aggregated_energy_cost_by_type = {}
        
        # List of vehicle reports
        vehicle_reports = []
        
        # Process each vehicle
        for vehicle in owned_vehicles:
            # Get servicing records
            servicings = VehicleServicing.objects.filter(
                vehicle=vehicle,
                date__gte=from_date,
                date__lte=to_date
            ).order_by('-date')
            
            servicing_count = servicings.count()
            servicing_amount = servicings.aggregate(total=Sum('amount'))['total'] or 0
            servicing_details = VehicleServicingListSerializer(servicings, many=True).data
            
            # Get expenses records
            expenses = VehicleExpenses.objects.filter(
                vehicle=vehicle,
                entry_date__gte=from_date,
                entry_date__lte=to_date
            ).order_by('-entry_date')
            
            expenses_count = expenses.count()
            expenses_amount = expenses.aggregate(total=Sum('amount'))['total'] or 0
            
            # Expenses by type
            expenses_by_type = {}
            for expense_type in ['part', 'fine']:
                type_expenses = expenses.filter(expenses_type=expense_type)
                type_amount = float(type_expenses.aggregate(total=Sum('amount'))['total'] or 0)
                expenses_by_type[expense_type] = type_amount
                # Aggregate to total
                if expense_type not in aggregated_expenses_by_type:
                    aggregated_expenses_by_type[expense_type] = 0.0
                aggregated_expenses_by_type[expense_type] += type_amount
            
            expenses_details = VehicleExpensesListSerializer(expenses, many=True).data
            
            # Get energy cost records
            energy_costs = VehicleEnergyCost.objects.filter(
                vehicle=vehicle,
                entry_date__gte=from_date,
                entry_date__lte=to_date
            ).order_by('-entry_date')
            
            energy_cost_count = energy_costs.count()
            energy_cost_amount = energy_costs.aggregate(total=Sum('amount'))['total'] or 0
            energy_cost_units = energy_costs.aggregate(total=Sum('total_unit'))['total'] or 0
            
            # Energy cost by type
            energy_cost_by_type = {}
            for energy_type in ['fuel', 'electric']:
                type_costs = energy_costs.filter(energy_type=energy_type)
                type_amount = float(type_costs.aggregate(total=Sum('amount'))['total'] or 0)
                energy_cost_by_type[energy_type] = type_amount
                # Aggregate to total
                if energy_type not in aggregated_energy_cost_by_type:
                    aggregated_energy_cost_by_type[energy_type] = 0.0
                aggregated_energy_cost_by_type[energy_type] += type_amount
            
            energy_cost_details = VehicleEnergyCostListSerializer(energy_costs, many=True).data
            
            # Add to aggregated totals
            total_servicing_count += servicing_count
            total_servicing_amount += float(servicing_amount)
            total_expenses_count += expenses_count
            total_expenses_amount += float(expenses_amount)
            total_energy_cost_count += energy_cost_count
            total_energy_cost_amount += float(energy_cost_amount)
            total_energy_cost_units += float(energy_cost_units)
            
            # Build vehicle report
            vehicle_report = {
                'vehicle': {
                    'id': vehicle.id,
                    'name': vehicle.name,
                    'imei': vehicle.imei,
                    'vehicle_no': vehicle.vehicleNo,
                },
                'servicing': {
                    'total_count': servicing_count,
                    'total_amount': float(servicing_amount),
                    'details': servicing_details
                },
                'expenses': {
                    'total_count': expenses_count,
                    'total_amount': float(expenses_amount),
                    'by_type': expenses_by_type,
                    'details': expenses_details
                },
                'energy_cost': {
                    'total_count': energy_cost_count,
                    'total_amount': float(energy_cost_amount),
                    'total_units': float(energy_cost_units),
                    'by_type': energy_cost_by_type,
                    'details': energy_cost_details
                }
            }
            vehicle_reports.append(vehicle_report)
        
        # Build aggregated report response
        report_data = {
            'total_days': total_days,
            'total_vehicles': len(vehicle_reports),
            'aggregated': {
                'servicing': {
                    'total_count': total_servicing_count,
                    'total_amount': total_servicing_amount,
                },
                'expenses': {
                    'total_count': total_expenses_count,
                    'total_amount': total_expenses_amount,
                    'by_type': aggregated_expenses_by_type,
                },
                'energy_cost': {
                    'total_count': total_energy_cost_count,
                    'total_amount': total_energy_cost_amount,
                    'total_units': total_energy_cost_units,
                    'by_type': aggregated_energy_cost_by_type,
                }
            },
            'vehicles': vehicle_reports
        }
        
        return success_response(report_data, 'All vehicles fleet report generated successfully')
    
    except Exception as e:
        return handle_api_exception(e)

