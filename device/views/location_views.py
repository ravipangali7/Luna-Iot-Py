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
        
        # Create location record
        location_obj = Location.objects.create(
            device=device,
            imei=data['imei'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            speed=data['speed'],
            course=data['course'],
            realTimeGps=data['real_time_gps'],
            satellite=data['satellite'],
            createdAt=data['created_at']
        )
        
        location_data = {
            'id': location_obj.id,
            'imei': location_obj.imei,
            'latitude': float(location_obj.latitude),
            'longitude': float(location_obj.longitude),
            'speed': float(location_obj.speed) if location_obj.speed else 0,
            'course': float(location_obj.course) if location_obj.course else 0,
            'satellite': location_obj.satellite,
            'realTimeGps': location_obj.realTimeGps,
            'createdAt': location_obj.createdAt.isoformat()
        }
        
        return success_response(
            data=location_data,
            message='Location created successfully'
        )
    except Exception as e:
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
                'realTimeGps': location.real_time_gps,
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
            location = Location.objects.filter(imei=imei).order_by('-created_at').first()
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
            'realTimeGps': location.real_time_gps,
            'createdAt': location.created_at.isoformat()
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
            created_at__range=[start, end]
        ).order_by('-created_at')
        
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
                'realTimeGps': location.real_time_gps,
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
        start = start.replace(hour=12, minute=0, second=1, microsecond=0)
        
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        end = end.replace(hour=23, minute=59, second=59, microsecond=999000)
        
        # Get location data
        locations = Location.objects.filter(
            imei=imei,
            created_at__range=[start, end]
        ).order_by('created_at')
        
        # Get status data with ignition off
        from device.models.status import Status
        statuses = Status.objects.filter(
            imei=imei,
            created_at__range=[start, end],
            ignition=False
        ).order_by('created_at')
        
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
                'realTimeGps': location.real_time_gps,
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
                'createdAt': status.created_at.isoformat()
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
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        start = start.replace(hour=12, minute=0, second=1, microsecond=0)
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
            created_at__range=[start, end]
        ).order_by('created_at')
        
        # Get status data
        from device.models.status import Status
        statuses = Status.objects.filter(
            imei=imei,
            created_at__range=[start, end]
        ).order_by('created_at')
        
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
        
        # Calculate average speed
        avg_speed = 0
        if total_locations > 0:
            total_speed = sum(float(loc.speed) if loc.speed else 0 for loc in locations)
            avg_speed = total_speed / total_locations
        
        # Calculate ignition statistics
        ignition_on_count = statuses.filter(ignition=True).count()
        ignition_off_count = statuses.filter(ignition=False).count()
        
        # Generate daily data
        daily_data = []
        current_date = start.date()
        end_date_obj = end.date()
        
        while current_date <= end_date_obj:
            day_locations = locations.filter(created_at__date=current_date)
            day_statuses = statuses.filter(created_at__date=current_date)
            
            daily_data.append({
                'date': current_date.isoformat(),
                'locations': day_locations.count(),
                'statuses': day_statuses.count(),
                'ignitionOn': day_statuses.filter(ignition=True).count(),
                'ignitionOff': day_statuses.filter(ignition=False).count()
            })
            
            current_date += timedelta(days=1)
        
        report_data = {
            'summary': {
                'totalLocations': total_locations,
                'totalStatuses': total_statuses,
                'totalDistance': round(total_distance, 2),
                'averageSpeed': round(avg_speed, 2),
                'ignitionOnCount': ignition_on_count,
                'ignitionOffCount': ignition_off_count
            },
            'dailyData': daily_data,
            'dateRange': {
                'start': start.isoformat(),
                'end': end.isoformat()
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
