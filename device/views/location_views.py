"""
Location Views
Handles location tracking endpoints
Matches Node.js location_controller.js functionality exactly
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta

from device.models.location import Location
from device.models.device import Device
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.exceptions.api_exceptions import NotFoundError, ValidationError


@api_view(['POST'])
@api_response
def create_location(request):
    """
    Create new location record
    For Node.js GT06 handler to send location data
    """
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['imei', 'latitude', 'longitude', 'speed', 'course', 'real_time_gps', 'satellite', 'created_at']
        for field in required_fields:
            if field not in data:
                return error_response(
                    message=f'Missing required field: {field}',
                    status_code=HTTP_STATUS['BAD_REQUEST']
                )
        
        # Check if device exists
        try:
            device = Device.objects.get(imei=data['imei'])
        except Device.DoesNotExist:
            return error_response(
                message='Device not found with IMEI: ' + data['imei'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Check if any vehicle with this IMEI is active
        from fleet.models import Vehicle
        active_vehicles = Vehicle.objects.filter(imei=data['imei'], is_active=True)
        if not active_vehicles.exists():
            return error_response(
                message='No active vehicle found with IMEI: ' + data['imei'],
                status_code=HTTP_STATUS['BAD_REQUEST']
            )

        
        # Convert timestamp to timezone-aware datetime object
        import pytz
        
        try:
            created_at_str = data['created_at']
            
            if created_at_str.endswith('Z'):
                # Remove Z and parse the datetime
                created_at_str = created_at_str[:-1]
                dt = datetime.fromisoformat(created_at_str)
                # Keep as naive datetime (Nepal time) - Django will treat it as Nepal time due to TIME_ZONE setting
                createdAt = dt
            else:
                # Handle other formats
                dt = datetime.fromisoformat(created_at_str.replace('Z', ''))
                createdAt = dt
        except Exception as dt_error:
            nepal_tz = pytz.timezone('Asia/Kathmandu')
            createdAt = datetime.now(nepal_tz)
        
        # Create location record
        try:
            location_obj = Location.objects.create(
                device=device,
                imei=data['imei'],
                latitude=data['latitude'],
                longitude=data['longitude'],
                speed=data['speed'],
                course=data['course'],
                realTimeGps=data['real_time_gps'],
                satellite=data['satellite'],
                createdAt=createdAt
            )
        except Exception as create_error:
            print("LOCATION: Error creating location record:", str(create_error))
            print("LOCATION: Error type:", type(create_error).__name__)
            raise create_error
        
        location_data = {
            'id': location_obj.id,
            'imei': location_obj.imei,
            'latitude': float(location_obj.latitude),
            'longitude': float(location_obj.longitude),
            'speed': float(location_obj.speed) if location_obj.speed else 0,
            'course': float(location_obj.course) if location_obj.course else 0,
            'satellite': location_obj.satellite,
            'realTimeGps': location_obj.realTimeGps,
            'createdAt': location_obj.createdAt
        }
        
        return success_response(
            data=location_data,
            message='Location created successfully'
        )
    except Exception as e:
        import traceback
        print("LOCATION: Full error traceback:")
        print(traceback.format_exc())
        print("LOCATION: Error message:", str(e))
        print("LOCATION: Error type:", type(e).__name__)
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@api_response
def get_location_by_imei(request, imei):
    """
    Get location history by IMEI
    Matches Node.js LocationController.getLocationByImei
    """
    try:
        locations = Location.objects.filter(imei=imei).order_by('-createdAt')
        locations_data = []
        
        for location in locations:
            locations_data.append({
                'id': location.id,
                'imei': location.imei,
                'latitude': float(location.latitude),
                'longitude': float(location.longitude),
                'speed': float(location.speed) if location.speed else 0,
                'course': float(location.course) if location.course else 0,
                'satellite': location.satellite,
                'realTimeGps': location.realTimeGps,
                'createdAt': location.createdAt.isoformat()
            })
        
        return success_response(
            data=locations_data,
            message=SUCCESS_MESSAGES['LOCATION_RETRIEVED']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@api_response
def get_latest_location(request, imei):
    """
    Get latest location by IMEI
    Matches Node.js LocationController.getLatestLocation
    """
    try:
        try:
            location = Location.objects.filter(imei=imei).order_by('-createdAt').first()
        except Location.DoesNotExist:
            return error_response(
                message='No location data found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        if not location:
            return error_response(
                message='No location data found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        location_data = {
            'id': location.id,
            'imei': location.imei,
            'latitude': float(location.latitude),
            'longitude': float(location.longitude),
            'speed': float(location.speed) if location.speed else 0,
            'course': float(location.course) if location.course else 0,
            'satellite': location.satellite,
            'realTimeGps': location.realTimeGps,
            'createdAt': location.createdAt.isoformat()
        }
        
        return success_response(
            data=location_data,
            message='Latest location retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@api_response
def get_location_by_date_range(request, imei):
    """
    Get location by date range
    Matches Node.js LocationController.getLocationByDateRange
    """
    try:
        start_date = request.GET.get('startDate')
        end_date = request.GET.get('endDate')
        
        if not start_date or not end_date:
            return error_response(
                message='Start date and end date are required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        locations = Location.objects.filter(
            imei=imei,
            createdAt__range=[start, end]
        ).order_by('-createdAt')
        
        locations_data = []
        for location in locations:
            locations_data.append({
                'id': location.id,
                'imei': location.imei,
                'latitude': float(location.latitude),
                'longitude': float(location.longitude),
                'speed': float(location.speed) if location.speed else 0,
                'course': float(location.course) if location.course else 0,
                'satellite': location.satellite,
                'realTimeGps': location.realTimeGps,
                'createdAt': location.createdAt.isoformat()
            })
        
        return success_response(
            data=locations_data,
            message='Location data retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@api_response
def get_combined_history_by_date_range(request, imei):
    """
    Get combined history by date range (location + status with ignition off)
    Matches Node.js LocationController.getCombinedHistoryByDateRange
    """
    try:
        start_date = request.GET.get('startDate')
        end_date = request.GET.get('endDate')
        
        if not start_date or not end_date:
            return error_response(
                message='Start date and end date are required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Set timezone-aware dates
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        start = start.replace(hour=0, minute=0, second=1, microsecond=0)
        
        end = datetime.fromisoformat(end_date.replace('Z', '+23:59'))
        end = end.replace(hour=23, minute=59, second=59, microsecond=999000)
        
        # Get location data
        locations = Location.objects.filter(
            imei=imei,
            createdAt__range=[start, end]
        ).order_by('createdAt')
        
        # Get status data with ignition off
        from device.models.status import Status
        statuses = Status.objects.filter(
            imei=imei,
            createdAt__range=[start, end],
            ignition=False
        ).order_by('createdAt')
        
        # Combine data
        combined_data = []
        
        # Add location data
        for location in locations:
            combined_data.append({
                'type': 'location',
                'id': location.id,
                'imei': location.imei,
                'latitude': float(location.latitude),
                'longitude': float(location.longitude),
                'speed': float(location.speed) if location.speed else 0,
                'course': float(location.course) if location.course else 0,
                'satellite': location.satellite,
                'realTimeGps': location.realTimeGps,
                'createdAt': location.createdAt.isoformat()
            })
        
        # Add status data
        for status in statuses:
            combined_data.append({
                'type': 'status',
                'id': status.id,
                'imei': status.imei,
                'battery': status.battery,
                'signal': status.signal,
                'ignition': status.ignition,
                'charging': status.charging,
                'relay': status.relay,
                'createdAt': status.createdAt.isoformat()
            })
        
        # Sort by created_at
        combined_data.sort(key=lambda x: x['createdAt'])
        
        return success_response(
            data=combined_data,
            message='Combined history data retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@api_response
def generate_report(request, imei):
    """
    Generate comprehensive report
    Matches Node.js LocationController.generateReport
    """
    try:
        start_date = request.GET.get('startDate')
        end_date = request.GET.get('endDate')
        
        if not start_date or not end_date:
            return error_response(
                message='Start date and end date are required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Validate date range (max 3 months)
         # Set timezone-aware dates
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        start = start.replace(hour=0, minute=0, second=1, microsecond=0)
        
        end = datetime.fromisoformat(end_date.replace('Z', '+23:59'))
        end = end.replace(hour=23, minute=59, second=59, microsecond=999000)
        
        three_months_ago = datetime.now() - timedelta(days=90)
        
        if start < three_months_ago:
            return error_response(
                message='Date range cannot exceed 3 months',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Get location data
        locations = Location.objects.filter(
            imei=imei,
            createdAt__range=[start, end]
        ).order_by('createdAt')
        
        # Get status data
        from device.models.status import Status
        statuses = Status.objects.filter(
            imei=imei,
            createdAt__range=[start, end]
        ).order_by('createdAt')
        
        # Calculate report statistics
        total_locations = locations.count()
        total_statuses = statuses.count()
        
        # Calculate total distance
        total_distance = 0
        if total_locations > 1:
            prev_location = None
            for location in locations:
                if prev_location:
                    # Simple distance calculation (Haversine formula would be better)
                    lat1, lon1 = float(prev_location.latitude), float(prev_location.longitude)
                    lat2, lon2 = float(location.latitude), float(location.longitude)
                    
                    # Rough distance calculation
                    import math
                    R = 6371  # Earth's radius in kilometers
                    dlat = math.radians(lat2 - lat1)
                    dlon = math.radians(lon2 - lon1)
                    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                    distance = R * c
                    total_distance += distance
                
                prev_location = location
        
        # Calculate comprehensive statistics
        speeds = [float(loc.speed) if loc.speed else 0 for loc in locations]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        max_speed = max(speeds) if speeds else 0
        
        # Calculate time-based statistics
        total_time_minutes = 0
        idle_time_minutes = 0
        running_time_minutes = 0
        overspeed_time_minutes = 0
        stop_time_minutes = 0
        
        # Get vehicle speed limit for overspeed calculation
        try:
            from fleet.models import Vehicle
            vehicle = Vehicle.objects.get(imei=imei)
            speed_limit = vehicle.speedLimit or 60  # Default to 60 km/h
        except:
            speed_limit = 60
        
        # Process status data for time calculations
        if statuses.exists():
            prev_status = None
            for status in statuses:
                if prev_status:
                    # Calculate time difference in minutes
                    time_diff = (status.createdAt - prev_status.createdAt).total_seconds() / 60
                    total_time_minutes += time_diff
                    
                    # Categorize time based on status
                    if prev_status.ignition:
                        # Get locations in this time period
                        period_locations = locations.filter(
                            createdAt__gte=prev_status.createdAt, 
                            createdAt__lt=status.createdAt
                        )
                        
                        if period_locations.exists():
                            # Check if vehicle was moving (speed > 0)
                            max_speed_in_period = max([float(loc.speed) if loc.speed else 0 for loc in period_locations], default=0)
                            
                            if max_speed_in_period > 0:
                                running_time_minutes += time_diff
                                
                                # Check for overspeed
                                if max_speed_in_period > speed_limit:
                                    overspeed_time_minutes += time_diff
                            else:
                                idle_time_minutes += time_diff
                        else:
                            # No location data in this period, assume idle
                            idle_time_minutes += time_diff
                    else:
                        stop_time_minutes += time_diff
                
                prev_status = status
        
        # Generate daily data with proper structure
        daily_data = []
        current_date = start.date()
        end_date_obj = end.date()
        
        while current_date <= end_date_obj:
            day_locations = locations.filter(createdAt__date=current_date)
            day_statuses = statuses.filter(createdAt__date=current_date)
            
            # Calculate daily statistics
            day_speeds = [float(loc.speed) if loc.speed else 0 for loc in day_locations]
            day_avg_speed = sum(day_speeds) / len(day_speeds) if day_speeds else 0
            day_max_speed = max(day_speeds) if day_speeds else 0
            
            # Calculate daily distance
            day_distance = 0
            if day_locations.count() > 1:
                prev_loc = None
                for loc in day_locations:
                    if prev_loc:
                        lat1, lon1 = float(prev_loc.latitude), float(prev_loc.longitude)
                        lat2, lon2 = float(loc.latitude), float(loc.longitude)
                        
                        R = 6371  # Earth's radius in kilometers
                        dlat = math.radians(lat2 - lat1)
                        dlon = math.radians(lon2 - lon1)
                        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
                        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                        distance = R * c
                        day_distance += distance
                    
                    prev_loc = loc
            
            daily_data.append({
                'date': current_date.isoformat(),
                'averageSpeed': round(day_avg_speed, 2),
                'maxSpeed': round(day_max_speed, 2),
                'totalKm': round(day_distance, 2),
                'locationCount': day_locations.count()
            })
            
            current_date += timedelta(days=1)
        
        # Create comprehensive report data matching frontend expectations
        report_data = {
            'stats': {
                'totalKm': round(total_distance, 2),
                'totalTime': round(total_time_minutes, 2),
                'averageSpeed': round(avg_speed, 2),
                'maxSpeed': round(max_speed, 2),
                'totalIdleTime': round(idle_time_minutes, 2),
                'totalRunningTime': round(running_time_minutes, 2),
                'totalOverspeedTime': round(overspeed_time_minutes, 2),
                'totalStopTime': round(stop_time_minutes, 2)
            },
            'dailyData': daily_data,
            'rawData': {
                'locations': [
                    {
                        'id': loc.id,
                        'imei': loc.imei,
                        'latitude': str(loc.latitude),
                        'longitude': str(loc.longitude),
                        'speed': float(loc.speed) if loc.speed else 0,
                        'course': float(loc.course) if loc.course else 0,
                        'realTimeGps': loc.realTimeGps,
                        'satellite': loc.satellite,
                        'createdAt': loc.createdAt.isoformat()
                    } for loc in locations
                ]
            }
        }
        
        return success_response(
            data=report_data,
            message='Report generated successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )
