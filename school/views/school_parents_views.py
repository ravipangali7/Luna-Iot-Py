"""
School Parents Views
Handles school parent management endpoints
"""
from rest_framework.decorators import api_view
from django.core.paginator import Paginator
from django.db.models import Q
from school.models import SchoolParent
from school.serializers import (
    SchoolParentSerializer,
    SchoolParentCreateSerializer,
    SchoolParentListSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError
from fleet.models import Vehicle, UserVehicle
from device.models import Device
from device.models.location import Location
from device.models.status import Status
from shared.models.recharge import Recharge
from datetime import datetime
import math


@api_view(['GET'])
@require_auth
@api_response
def get_all_school_parents(request):
    """Get all school parents with pagination and filtering"""
    try:
        search_query = request.GET.get('search', '').strip()
        institute_filter = request.GET.get('institute_id', '').strip()
        bus_filter = request.GET.get('bus_id', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        school_parents = SchoolParent.objects.select_related('parent').prefetch_related('school_buses').all()
        
        if search_query:
            school_parents = school_parents.filter(
                Q(parent__name__icontains=search_query) |
                Q(parent__phone__icontains=search_query)
            )
        
        if institute_filter:
            school_parents = school_parents.filter(
                school_buses__institute_id=institute_filter
            ).distinct()
        
        if bus_filter:
            school_parents = school_parents.filter(school_buses__id=bus_filter).distinct()
        
        school_parents = school_parents.order_by('-created_at')
        
        paginator = Paginator(school_parents, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = SchoolParentListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'School parents retrieved successfully'),
            data={
                'school_parents': serializer.data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'page_size': page_size,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_school_parent_by_id(request, parent_id):
    """Get school parent by ID"""
    try:
        try:
            school_parent = SchoolParent.objects.select_related('parent').prefetch_related('school_buses').get(id=parent_id)
        except SchoolParent.DoesNotExist:
            raise NotFoundError("School parent not found")
        
        serializer = SchoolParentSerializer(school_parent)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'School parent retrieved successfully')
        )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_school_parents_by_institute(request, institute_id):
    """Get school parents by institute"""
    try:
        school_parents = SchoolParent.objects.select_related('parent').prefetch_related('school_buses').filter(
            school_buses__institute_id=institute_id
        ).distinct().order_by('-created_at')
        
        serializer = SchoolParentListSerializer(school_parents, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'School parents retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_school_parents_by_bus(request, bus_id):
    """Get school parents by bus"""
    try:
        school_parents = SchoolParent.objects.select_related('parent').prefetch_related('school_buses').filter(
            school_buses__id=bus_id
        ).distinct().order_by('-created_at')
        
        serializer = SchoolParentListSerializer(school_parents, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'School parents retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


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


def calculate_today_km(imei):
    """
    Calculate today's kilometers for a vehicle based on location data
    """
    try:
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        # Get today's location data ordered by time
        locations = Location.objects.filter(
            imei=imei,
            createdAt__gte=start_of_day,
            createdAt__lte=end_of_day
        ).order_by('createdAt')
        
        if len(locations) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(locations)):
            prev_loc = locations[i-1]
            curr_loc = locations[i]
            
            distance = calculate_distance(
                prev_loc.latitude, prev_loc.longitude,
                curr_loc.latitude, curr_loc.longitude
            )
            total_distance += distance
        
        return round(total_distance, 2)
    except Exception as e:
        print(f"Error calculating today's km for {imei}: {e}")
        return 0.0


@api_view(['GET'])
@require_auth
@api_response
def get_my_school_vehicles(request):
    """
    Get vehicles associated with the logged-in school parent through school_parent -> school_buses -> vehicle relationship
    Returns paginated vehicle data with the same structure as get_vehicles_paginated()
    """
    try:
        user = request.user
        
        # Get page number from query parameters, default to 1
        page_number = int(request.GET.get('page', 1))
        page_size = 25  # Fixed page size to match frontend
        
        # Check if user is a school parent
        school_parents = SchoolParent.objects.filter(parent=user).prefetch_related('school_buses__bus')
        
        if not school_parents.exists():
            # Return empty result if user is not a school parent
            pagination_info = {
                'current_page': 1,
                'total_pages': 0,
                'total_items': 0,
                'page_size': page_size,
                'has_next': False,
                'has_previous': False,
                'next_page': None,
                'previous_page': None
            }
            
            response_data = {
                'vehicles': [],
                'pagination': pagination_info
            }
            
            return success_response(
                response_data,
                'No school vehicles found for this user'
            )
        
        # Get all vehicles from school buses associated with this school parent
        vehicle_ids = set()
        for school_parent in school_parents:
            for school_bus in school_parent.school_buses.all():
                # Only include active vehicles that are assigned as school buses
                if school_bus.bus and school_bus.bus.is_active:
                    vehicle_ids.add(school_bus.bus.id)
        
        # If no vehicles found, return empty result
        if not vehicle_ids:
            pagination_info = {
                'current_page': 1,
                'total_pages': 0,
                'total_items': 0,
                'page_size': page_size,
                'has_next': False,
                'has_previous': False,
                'next_page': None,
                'previous_page': None
            }
            
            response_data = {
                'vehicles': [],
                'pagination': pagination_info
            }
            
            return success_response(
                response_data,
                'No school vehicles found for this user'
            )
        
        # Get vehicles with complete data - only vehicles that are in school_buses
        vehicles = Vehicle.objects.filter(
            id__in=vehicle_ids,
            is_active=True
        ).select_related('device').prefetch_related('userVehicles__user').distinct()
        
        # Create paginator
        paginator = Paginator(vehicles, page_size)
        
        # Get the requested page
        try:
            page_obj = paginator.get_page(page_number)
        except:
            return error_response('Invalid page number', HTTP_STATUS['BAD_REQUEST'])
        
        vehicles_data = []
        for vehicle in page_obj:
            # Get all users with access to this vehicle (userVehicles format)
            user_vehicles = []
            for uv in vehicle.userVehicles.all():
                user_vehicles.append({
                    'id': uv.id,
                    'userId': uv.user.id,
                    'vehicleId': uv.vehicle.id,
                    'isMain': uv.isMain,
                    'user': {
                        'id': uv.user.id,
                        'name': uv.user.name,
                        'phone': uv.user.phone,
                        'status': 'active',  # Default status
                        'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in uv.user.groups.all()],
                        'createdAt': uv.createdAt.isoformat() if uv.createdAt else None,
                        'updatedAt': uv.createdAt.isoformat() if uv.createdAt else None
                    },
                    'createdAt': uv.createdAt.isoformat() if uv.createdAt else None,
                    'allAccess': uv.allAccess,
                    'liveTracking': uv.liveTracking,
                    'history': uv.history,
                    'report': uv.report,
                    'vehicleProfile': uv.vehicleProfile,
                    'events': uv.events,
                    'geofence': uv.geofence,
                    'edit': uv.edit,
                    'shareTracking': uv.shareTracking,
                    'notification': uv.notification,
                    'relay': getattr(uv, 'relay', False)
                })
            
            # Current user's single userVehicle convenience object
            try:
                current_user_uv = vehicle.userVehicles.filter(user=user).first()
            except Exception:
                current_user_uv = None

            user_vehicle_single = {
                'isMain': current_user_uv.isMain if current_user_uv else False,
                'allAccess': current_user_uv.allAccess if current_user_uv else False,
                'liveTracking': current_user_uv.liveTracking if current_user_uv else False,
                'history': current_user_uv.history if current_user_uv else False,
                'report': current_user_uv.report if current_user_uv else False,
                'vehicleProfile': current_user_uv.vehicleProfile if current_user_uv else False,
                'events': current_user_uv.events if current_user_uv else False,
                'geofence': current_user_uv.geofence if current_user_uv else False,
                'edit': current_user_uv.edit if current_user_uv else False,
                'shareTracking': current_user_uv.shareTracking if current_user_uv else False,
                'notification': current_user_uv.notification if current_user_uv else False,
                'relay': getattr(current_user_uv, 'relay', False) if current_user_uv else False
            } if current_user_uv else None

            # Get main customer (user with isMain=True)
            main_customer = None
            for uv in vehicle.userVehicles.all():
                if uv.isMain:
                    main_customer = {
                        'id': uv.id,
                        'userId': uv.user.id,
                        'vehicleId': uv.vehicle.id,
                        'isMain': uv.isMain,
                        'user': {
                            'id': uv.user.id,
                            'name': uv.user.name,
                            'phone': uv.user.phone,
                            'status': 'active',  # Default status
                            'roles': [{'id': group.id, 'name': group.name, 'description': ''} for group in uv.user.groups.all()],
                            'createdAt': uv.user.created_at.isoformat() if uv.user.created_at else None,
                            'updatedAt': uv.user.updated_at.isoformat() if uv.user.updated_at else None
                        },
                        'createdAt': uv.createdAt.isoformat() if uv.createdAt else None,
                        'allAccess': uv.allAccess,
                        'liveTracking': uv.liveTracking,
                        'history': uv.history,
                        'report': uv.report,
                        'vehicleProfile': uv.vehicleProfile,
                        'events': uv.events,
                        'geofence': uv.geofence,
                        'edit': uv.edit,
                        'shareTracking': uv.shareTracking,
                        'notification': uv.notification,
                        'relay': getattr(uv, 'relay', False)
                    }
                    break
            
            # Get latest recharge info
            try:
                latest_recharge_obj = Recharge.objects.filter(device=vehicle.device).order_by('-createdAt').first()
                latest_recharge = {
                    'id': latest_recharge_obj.id,
                    'deviceId': latest_recharge_obj.device.id,
                    'amount': float(latest_recharge_obj.amount),
                    'createdAt': latest_recharge_obj.createdAt.isoformat()
                } if latest_recharge_obj else None
            except Exception as e:
                latest_recharge = None
            
            # Calculate today's km
            today_km = calculate_today_km(vehicle.imei)
            
            # Get latest status
            try:
                latest_status_obj = Status.objects.filter(imei=vehicle.imei).order_by('-createdAt').first()
                latest_status = {
                    'id': latest_status_obj.id,
                    'imei': latest_status_obj.imei,
                    'battery': latest_status_obj.battery,
                    'signal': latest_status_obj.signal,
                    'ignition': latest_status_obj.ignition,
                    'charging': latest_status_obj.charging,
                    'relay': latest_status_obj.relay,
                    'createdAt': latest_status_obj.createdAt.isoformat(),
                    'updatedAt': latest_status_obj.updatedAt.isoformat()
                } if latest_status_obj else None
            except Exception as e:
                latest_status = None
            
            # Get latest location
            try:
                latest_location_obj = Location.objects.filter(imei=vehicle.imei).order_by('-createdAt').first()
                latest_location = {
                    'id': latest_location_obj.id,
                    'imei': latest_location_obj.imei,
                    'latitude': float(latest_location_obj.latitude),
                    'longitude': float(latest_location_obj.longitude),
                    'speed': latest_location_obj.speed,
                    'course': latest_location_obj.course,
                    'satellite': latest_location_obj.satellite,
                    'realTimeGps': latest_location_obj.realTimeGps,
                    'createdAt': latest_location_obj.createdAt.isoformat(),
                    'updatedAt': latest_location_obj.updatedAt.isoformat()
                } if latest_location_obj else None
            except Exception as e:
                latest_location = None
            
            vehicle_data = {
                'id': vehicle.id,
                'imei': vehicle.imei,
                'name': vehicle.name,
                'vehicleNo': vehicle.vehicleNo,
                'vehicleType': vehicle.vehicleType,
                'odometer': float(vehicle.odometer),
                'mileage': float(vehicle.mileage),
                'minimumFuel': float(vehicle.minimumFuel),
                'speedLimit': vehicle.speedLimit,
                'expireDate': vehicle.expireDate.isoformat() if vehicle.expireDate else None,
                'is_active': vehicle.is_active,
                'createdAt': vehicle.createdAt.isoformat() if vehicle.createdAt else None,
                'updatedAt': vehicle.updatedAt.isoformat() if vehicle.updatedAt else None,
                'device': {
                    'id': vehicle.device.id,
                    'imei': vehicle.device.imei,
                    'phone': vehicle.device.phone,
                    'sim': vehicle.device.sim,
                    'protocol': vehicle.device.protocol,
                    'iccid': vehicle.device.iccid,
                    'model': vehicle.device.model
                } if vehicle.device else None,
                'userVehicles': user_vehicles,
                'userVehicle': user_vehicle_single,
                'mainCustomer': main_customer,
                'latestRecharge': latest_recharge,
                'latestStatus': latest_status,
                'latestLocation': latest_location,
                'todayKm': today_km,
                'ownershipType': 'Own' if current_user_uv and current_user_uv.isMain else 'Shared' if current_user_uv else 'Customer'
            }
            vehicles_data.append(vehicle_data)
        
        # Prepare pagination info
        pagination_info = {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None
        }
        
        response_data = {
            'vehicles': vehicles_data,
            'pagination': pagination_info
        }
        
        return success_response(response_data, 'School vehicles retrieved successfully')
    
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_super_admin
@api_response
def create_school_parent(request):
    """Create new school parent"""
    try:
        serializer = SchoolParentCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            school_parent = serializer.save()
            response_serializer = SchoolParentSerializer(school_parent)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'School parent created successfully'),
                status_code=HTTP_STATUS['CREATED']
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['PUT'])
@require_super_admin
@api_response
def update_school_parent(request, parent_id):
    """Update school parent"""
    try:
        try:
            school_parent = SchoolParent.objects.get(id=parent_id)
        except SchoolParent.DoesNotExist:
            raise NotFoundError("School parent not found")
        
        serializer = SchoolParentCreateSerializer(school_parent, data=request.data)
        
        if serializer.is_valid():
            school_parent = serializer.save()
            response_serializer = SchoolParentSerializer(school_parent)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'School parent updated successfully')
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['DELETE'])
@require_super_admin
@api_response
def delete_school_parent(request, parent_id):
    """Delete school parent"""
    try:
        try:
            school_parent = SchoolParent.objects.get(id=parent_id)
        except SchoolParent.DoesNotExist:
            raise NotFoundError("School parent not found")
        
        parent_name = school_parent.parent.name or school_parent.parent.phone
        school_parent.delete()
        
        return success_response(
            data={'id': parent_id},
            message=f"School parent '{parent_name}' deleted successfully"
        )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['PUT'])
@require_auth
@api_response
def update_my_location(request):
    """
    Update logged-in school parent's location (latitude/longitude)
    """
    try:
        user = request.user
        
        # Get school parent for this user
        try:
            school_parent = SchoolParent.objects.get(parent=user)
        except SchoolParent.DoesNotExist:
            return error_response(
                message='User is not a school parent',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Get latitude and longitude from request
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        # Validate required fields
        if latitude is None or longitude is None:
            return error_response(
                message='Latitude and longitude are required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Validate latitude range (-90 to 90)
        try:
            latitude_decimal = float(latitude)
            if latitude_decimal < -90 or latitude_decimal > 90:
                return error_response(
                    message='Latitude must be between -90 and 90',
                    status_code=HTTP_STATUS['BAD_REQUEST']
                )
        except (ValueError, TypeError):
            return error_response(
                message='Latitude must be a valid number',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Validate longitude range (-180 to 180)
        try:
            longitude_decimal = float(longitude)
            if longitude_decimal < -180 or longitude_decimal > 180:
                return error_response(
                    message='Longitude must be between -180 and 180',
                    status_code=HTTP_STATUS['BAD_REQUEST']
                )
        except (ValueError, TypeError):
            return error_response(
                message='Longitude must be a valid number',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Update location
        school_parent.latitude = latitude_decimal
        school_parent.longitude = longitude_decimal
        school_parent.save()
        
        # Return updated school parent data
        serializer = SchoolParentSerializer(school_parent)
        
        return success_response(
            data=serializer.data,
            message='Location updated successfully'
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )

