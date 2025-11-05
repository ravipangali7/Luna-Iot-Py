"""
Dashboard Views
Handles dashboard statistics endpoints
"""
from rest_framework.decorators import api_view
from django.db.models import Count, Q
from django.core.cache import cache
from django.conf import settings
from datetime import datetime
import requests
import json
import math

from core.models.user import User
from core.models.my_setting import MySetting
from device.models.device import Device
from device.models.location import Location
from device.models.status import Status
from device.models.buzzer_status import BuzzerStatus
from device.models.sos_status import SosStatus
from fleet.models.vehicle import Vehicle
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth


def get_sms_balance():
    """
    Fetch SMS balance from external API with caching
    Returns cached value if available, otherwise fetches from API
    """
    cache_key = 'sms_balance'
    cached_balance = cache.get(cache_key)
    
    if cached_balance is not None:
        return cached_balance
    
    try:
        api_key = "568383D0C5AA82"
        url = f"https://sms.kaichogroup.com/miscapi/{api_key}/getBalance/true/"
        
        print(f"Fetching SMS balance from: {url}")
        
        # Use shorter timeout to prevent blocking
        response = requests.get(url, timeout=5)
        print(f"SMS API Response Status: {response.status_code}")
        
        response.raise_for_status()
        
        # Try to get text first to see raw response
        response_text = response.text
        print(f"SMS API Raw Response: {response_text}")
        
        # Check if response starts with ERR:
        if response_text.startswith("ERR:"):
            print(f"SMS API Error: {response_text}")
            # Cache error result for shorter time (1 minute) to avoid repeated failures
            cache.set(cache_key, 0, 60)
            return 0
        
        # Try to parse as JSON
        try:
            data = response.json()
            print(f"SMS API JSON Response: {data}")
        except json.JSONDecodeError:
            print("SMS API response is not valid JSON")
            cache.set(cache_key, 0, 60)
            return 0
        
        # Handle the correct response format: [{"ROUTE_ID":"xx","ROUTE":"<name>","BALANCE":"<balance>"}]
        if isinstance(data, list) and len(data) > 0:
            # Sum up all balances from all routes
            total_balance = 0
            for route in data:
                if isinstance(route, dict) and 'BALANCE' in route:
                    try:
                        balance = float(route['BALANCE'])
                        total_balance += balance
                        print(f"Route {route.get('ROUTE', 'Unknown')}: {balance} SMS")
                    except (ValueError, TypeError):
                        print(f"Invalid balance format for route: {route}")
                        continue
            
            print(f"Total SMS Balance: {total_balance}")
            # Cache the result
            cache_timeout = getattr(settings, 'CACHE_TIMEOUT_SMS_BALANCE', 600)
            cache.set(cache_key, total_balance, cache_timeout)
            return total_balance
        else:
            print("Unexpected response format - not a list or empty list")
            cache.set(cache_key, 0, 60)
            return 0
        
    except requests.exceptions.Timeout:
        print("SMS API request timed out, returning 0")
        # Cache 0 for short time to avoid repeated timeouts
        cache.set(cache_key, 0, 60)
        return 0
    except Exception as e:
        print(f"Error fetching SMS balance: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return 0 on error
        return 0


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points using Haversine formula
    Returns distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def calculate_today_km():
    """
    Calculate total kilometers traveled today from all location data
    Optimized with caching and memory-efficient iteration
    """
    cache_key = 'today_km'
    cached_km = cache.get(cache_key)
    
    if cached_km is not None:
        return cached_km
    
    try:
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        # Use iterator() to avoid loading all data into memory at once
        # Only select necessary fields for better performance
        locations = Location.objects.filter(
            createdAt__gte=start_of_day,
            createdAt__lte=end_of_day
        ).order_by('imei', 'createdAt').only('imei', 'latitude', 'longitude').iterator(chunk_size=1000)
        
        total_distance = 0.0
        current_imei = None
        prev_loc = None
        location_count = 0
        
        for loc in locations:
            location_count += 1
            
            # If this is a new IMEI, reset previous location
            if current_imei != loc.imei:
                current_imei = loc.imei
                prev_loc = loc
                continue
            
            # Calculate distance between consecutive locations for same IMEI
            if prev_loc:
                distance = calculate_distance(
                    float(prev_loc.latitude), float(prev_loc.longitude),
                    float(loc.latitude), float(loc.longitude)
                )
                total_distance += distance
            
            prev_loc = loc
        
        if location_count < 2:
            result = 0.0
        else:
            result = round(total_distance, 2)
        
        # Cache the result
        cache_timeout = getattr(settings, 'CACHE_TIMEOUT_TODAY_KM', 120)
        cache.set(cache_key, result, cache_timeout)
        
        return result
    except Exception as e:
        print(f"Error calculating today's km: {e}")
        return 0.0


@api_view(['GET'])
@require_auth
@api_response
def get_dashboard_stats(request):
    """
    Get dashboard statistics
    Returns comprehensive stats for the dashboard with caching
    """
    # Check cache first
    cache_key = 'dashboard_stats'
    cached_stats = cache.get(cache_key)
    
    if cached_stats is not None:
        return success_response(
            data=cached_stats,
            message='Dashboard statistics retrieved successfully'
        )
    
    try:
        current_date = datetime.now()
        today = current_date.date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        # Optimize user statistics - get both counts in one query
        user_stats = User.objects.aggregate(
            total_users=Count('id'),
            active_users=Count('id', filter=Q(is_active=True))
        )
        total_users = user_stats['total_users'] or 0
        active_users = user_stats['active_users'] or 0
        
        # Get user role statistics - more robust approach
        user_role_stats = User.objects.filter(
            groups__isnull=False
        ).values('groups__name').annotate(
            count=Count('id')
        ).values('groups__name', 'count')
        
        # Convert to dictionary for easier access
        role_counts = {item['groups__name']: item['count'] for item in user_role_stats if item['groups__name']}
        
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
        
        # Vehicle statistics - combine queries where possible
        vehicle_stats = Vehicle.objects.aggregate(
            total_vehicles=Count('id'),
            expired_vehicles=Count('id', filter=Q(expireDate__lt=current_date)),
            today_added_vehicles=Count('id', filter=Q(createdAt__date=today))
        )
        total_vehicles = vehicle_stats['total_vehicles'] or 0
        expired_vehicles = vehicle_stats['expired_vehicles'] or 0
        today_added_vehicles = vehicle_stats['today_added_vehicles'] or 0
        
        # Fetch SMS balance from external API (cached)
        sms_balance = get_sms_balance()
        
        # Get MyPay balance from MySetting
        mypay_balance = MySetting.get_balance()
        
        today_transaction = 0  # Hardcoded as requested
        
        # Total hits today - optimize by using date range instead of date lookup
        # This is more efficient as it can use indexes better
        today_hits = (
            Location.objects.filter(createdAt__gte=start_of_day, createdAt__lte=end_of_day).count() +
            Status.objects.filter(createdAt__gte=start_of_day, createdAt__lte=end_of_day).count() +
            BuzzerStatus.objects.filter(createdAt__gte=start_of_day, createdAt__lte=end_of_day).count() +
            SosStatus.objects.filter(createdAt__gte=start_of_day, createdAt__lte=end_of_day).count()
        )
        
        # Calculate today's total kilometers (cached)
        today_km = calculate_today_km()
        
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
            'totalBalance': mypay_balance,  # MyPay balance from mobile topup
            'serverBalance': 0,  # Placeholder - would need server balance service
            'todayAddedVehicles': today_added_vehicles,
            'todayTransaction': today_transaction,
            'totalHitsToday': today_hits,
            'todayKm': today_km,
        }
        
        # Cache the response
        cache_timeout = getattr(settings, 'CACHE_TIMEOUT_DASHBOARD_STATS', 300)
        cache.set(cache_key, stats_data, cache_timeout)
        
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
