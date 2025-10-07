"""
Dashboard Views
Handles dashboard statistics endpoints
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q
from datetime import datetime
import requests
import json

from core.models.user import User
from device.models.device import Device
from fleet.models.vehicle import Vehicle
from django.contrib.auth.models import Group
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth


def get_sms_balance():
    """
    Fetch SMS balance from external API
    """
    try:
        api_key = "568383D0C5AA82"
        url = f"https://sms.kaichogroup.com/miscapi/{api_key}/getBalance/true/"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract balance from response
        # The API might return different formats, so we'll handle common cases
        if isinstance(data, dict):
            # Try different possible keys for balance
            balance = (
                data.get('balance', 0) or 
                data.get('Balance', 0) or 
                data.get('BALANCE', 0) or 
                data.get('credit', 0) or 
                data.get('Credit', 0) or 
                data.get('CREDIT', 0) or
                0
            )
        elif isinstance(data, (int, float)):
            balance = data
        else:
            balance = 0
            
        return float(balance) if balance else 0
        
    except Exception as e:
        print(f"Error fetching SMS balance: {str(e)}")
        return 0


@api_view(['GET'])
@require_auth
@api_response
def get_dashboard_stats(request):
    """
    Get dashboard statistics
    Returns comprehensive stats for the dashboard
    """
    try:
        # User statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        # Get user role statistics - more robust approach
        user_role_stats = User.objects.filter(
            groups__isnull=False
        ).values('groups__name').annotate(
            count=Count('id')
        ).values('groups__name', 'count')
        
        # Convert to dictionary for easier access
        role_counts = {item['groups__name']: item['count'] for item in user_role_stats if item['groups__name']}
        
        # Debug: Print available roles for troubleshooting
        print(f"Available roles in system: {role_counts}")
        
        # Try different possible role names
        total_dealers = (
            role_counts.get('DEALER', 0) + 
            role_counts.get('dealer', 0) + 
            role_counts.get('Dealer', 0)
        )
        total_customers = (
            role_counts.get('CUSTOMER', 0) + 
            role_counts.get('customer', 0) + 
            role_counts.get('Customer', 0)
        )
        
        # Device statistics
        total_devices = Device.objects.count()
        
        # Vehicle statistics
        total_vehicles = Vehicle.objects.count()
        
        # Count expired vehicles (vehicles with expireDate in the past)
        current_date = datetime.now()
        expired_vehicles = Vehicle.objects.filter(
            expireDate__lt=current_date
        ).count()
        
        # Fetch SMS balance from external API
        sms_balance = get_sms_balance()
        
        # Prepare response data
        stats_data = {
            'totalUsers': total_users,
            'activeUsers': active_users,
            'totalDealers': total_dealers,
            'totalCustomers': total_customers,
            'totalDevices': total_devices,
            'totalVehicles': total_vehicles,
            'expiredVehicles': expired_vehicles,
            'totalSms': sms_balance,  # Real SMS balance from API
            'totalBalance': 0,  # Placeholder - would need balance service
            'serverBalance': 0,  # Placeholder - would need server balance service
        }
        
        return success_response(
            data=stats_data,
            message='Dashboard statistics retrieved successfully'
        )
        
    except Exception as e:
        return error_response(
            message=f'Error retrieving dashboard statistics: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_user_stats(request):
    """
    Get user-specific statistics
    """
    try:
        # Get user role statistics
        user_role_stats = User.objects.values('groups__name').annotate(
            count=Count('id')
        ).values('groups__name', 'count')
        
        # Convert to dictionary for easier access
        role_counts = {item['groups__name']: item['count'] for item in user_role_stats if item['groups__name']}
        
        stats_data = {
            'totalUsers': User.objects.count(),
            'activeUsers': User.objects.filter(is_active=True).count(),
            'inactiveUsers': User.objects.filter(is_active=False).count(),
            'totalDealers': role_counts.get('DEALER', 0),
            'totalCustomers': role_counts.get('CUSTOMER', 0),
            'totalAdmins': role_counts.get('ADMIN', 0),
            'roleBreakdown': role_counts
        }
        
        return success_response(
            data=stats_data,
            message='User statistics retrieved successfully'
        )
        
    except Exception as e:
        return error_response(
            message=f'Error retrieving user statistics: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_device_stats(request):
    """
    Get device-specific statistics
    """
    try:
        stats_data = {
            'totalDevices': Device.objects.count(),
            'devicesByModel': dict(Device.objects.values('model').annotate(
                count=Count('id')
            ).values_list('model', 'count')),
            'devicesByProtocol': dict(Device.objects.values('protocol').annotate(
                count=Count('id')
            ).values_list('protocol', 'count')),
            'devicesBySim': dict(Device.objects.values('sim').annotate(
                count=Count('id')
            ).values_list('sim', 'count'))
        }
        
        return success_response(
            data=stats_data,
            message='Device statistics retrieved successfully'
        )
        
    except Exception as e:
        return error_response(
            message=f'Error retrieving device statistics: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_vehicle_stats(request):
    """
    Get vehicle-specific statistics
    """
    try:
        current_date = datetime.now()
        
        stats_data = {
            'totalVehicles': Vehicle.objects.count(),
            'activeVehicles': Vehicle.objects.filter(is_active=True).count(),
            'inactiveVehicles': Vehicle.objects.filter(is_active=False).count(),
            'expiredVehicles': Vehicle.objects.filter(expireDate__lt=current_date).count(),
            'vehiclesByType': dict(Vehicle.objects.values('vehicleType').annotate(
                count=Count('id')
            ).values_list('vehicleType', 'count')),
            'vehiclesExpiringSoon': Vehicle.objects.filter(
                expireDate__gte=current_date,
                expireDate__lte=current_date.replace(day=current_date.day + 30)
            ).count()
        }
        
        return success_response(
            data=stats_data,
            message='Vehicle statistics retrieved successfully'
        )
        
    except Exception as e:
        return error_response(
            message=f'Error retrieving vehicle statistics: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )
