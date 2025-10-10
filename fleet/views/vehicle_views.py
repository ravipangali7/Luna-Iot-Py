from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
import json
import re

from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.auth_decorators import require_auth, require_role
from api_common.constants.api_constants import HTTP_STATUS
from api_common.utils.validation_utils import validate_required_fields, validate_imei
from api_common.utils.exception_utils import handle_api_exception

from fleet.models import Vehicle, UserVehicle
from device.models import Device, UserDevice
from device.models.location import Location
from device.models.status import Status
from core.models import User
from shared.models.recharge import Recharge
from datetime import datetime, timedelta
import math


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


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_all_vehicles(request):
    """
    Get all vehicles with complete data (ownership, today's km, latest status and location)
    """
    try:
        user = request.user
        
        # Get vehicles based on user role
        user_group = user.groups.first()
        if user_group and user_group.name == 'Super Admin':
            vehicles = Vehicle.objects.select_related('device').prefetch_related('userVehicles__user').all()
        else:
            # Get vehicles where user has access
            vehicles = Vehicle.objects.filter(
                Q(userVehicles__user=user) |  # Direct vehicle access
                Q(device__userDevices__user=user)  # Device access
            ).select_related('device').prefetch_related('userVehicles__user').distinct()
        
        vehicles_data = []
        for vehicle in vehicles:
            # Get user vehicle relationship
            user_vehicle = vehicle.userVehicles.filter(user=user).first()
            
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
                    'createdAt': latest_status_obj.createdAt.isoformat()
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
                    'createdAt': latest_location_obj.createdAt.isoformat()
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
                'userVehicle': {
                    'isMain': user_vehicle.isMain if user_vehicle else False,
                    'allAccess': user_vehicle.allAccess if user_vehicle else False,
                    'liveTracking': user_vehicle.liveTracking if user_vehicle else False,
                    'history': user_vehicle.history if user_vehicle else False,
                    'report': user_vehicle.report if user_vehicle else False,
                    'vehicleProfile': user_vehicle.vehicleProfile if user_vehicle else False,
                    'events': user_vehicle.events if user_vehicle else False,
                    'geofence': user_vehicle.geofence if user_vehicle else False,
                    'edit': user_vehicle.edit if user_vehicle else False,
                    'shareTracking': user_vehicle.shareTracking if user_vehicle else False,
                    'notification': user_vehicle.notification if user_vehicle else False,
                    'relay': user_vehicle.relay if user_vehicle else False
                } if user_vehicle else None,
                'todayKm': today_km,
                'latestStatus': latest_status,
                'latestLocation': latest_location,
                'ownershipType': 'Own' if user_vehicle and user_vehicle.isMain else 'Shared' if user_vehicle else 'Customer'
            }
            vehicles_data.append(vehicle_data)
        
        return success_response(vehicles_data, 'Vehicles retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"]) 
@require_auth
def get_all_vehicles_detailed(request):
    """
    Get all vehicles with detailed data for table display (includes device, user, recharge info)
    """
    try:
        user = request.user
        
        # Get vehicles based on user role
        user_group = user.groups.first()
        if user_group and user_group.name == 'Super Admin':
            vehicles = Vehicle.objects.select_related('device').prefetch_related('userVehicles__user').all()
        else:
            # Get vehicles where user has access
            vehicles = Vehicle.objects.filter(
                Q(userVehicles__user=user) |  # Direct vehicle access
                Q(device__userDevices__user=user)  # Device access
            ).select_related('device').prefetch_related('userVehicles__user').distinct()
        
        vehicles_data = []
        for vehicle in vehicles:
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
                        'createdAt': uv.createdAt.isoformat(),
                        'updatedAt': uv.createdAt.isoformat()
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
            
            # Get current user's userVehicle (convenience single object for clients)
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
                    'createdAt': latest_status_obj.createdAt.isoformat()
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
                    'createdAt': latest_location_obj.createdAt.isoformat()
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
                'todayKm': today_km
            }
            vehicles_data.append(vehicle_data)
        
        return success_response(vehicles_data, 'Detailed vehicles retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_vehicle_by_imei(request, imei):
    """
    Get vehicle by IMEI with complete data and role-based access
    """
    try:
        user = request.user
        print(f"DEBUG: get_vehicle_by_imei called with IMEI: {imei} for user: {user.username}")
        
        # Get vehicle with access check
        user_group = user.groups.first()
        if user_group and user_group.name == 'Super Admin':
            vehicle = Vehicle.objects.select_related('device').prefetch_related('userVehicles__user').filter(imei=imei).first()
            print(f"DEBUG: Super Admin - Found vehicle: {vehicle.imei if vehicle else 'None'}")
        else:
            # First check if the specific IMEI exists and user has access to it
            vehicle = Vehicle.objects.filter(
                imei=imei
            ).filter(
                Q(userVehicles__user=user) |  # Direct vehicle access
                Q(device__userDevices__user=user)  # Device access
            ).select_related('device').prefetch_related('userVehicles__user').first()
            print(f"DEBUG: Customer - Found vehicle: {vehicle.imei if vehicle else 'None'}")
        
        if not vehicle:
            return error_response('Vehicle not found or access denied', HTTP_STATUS['NOT_FOUND'])
        
        # Get user vehicle relationship
        user_vehicle = vehicle.userVehicles.filter(user=user).first()
        
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
                'createdAt': latest_status_obj.createdAt.isoformat()
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
                'createdAt': latest_location_obj.createdAt.isoformat()
            } if latest_location_obj else None
        except Exception as e:
            latest_location = None
        
        # Get all users with access to this vehicle
        users_with_access = []
        for uv in vehicle.userVehicles.all():
            users_with_access.append({
                'id': uv.user.id,
                'name': uv.user.name,
                'phone': uv.user.phone,
                'isMain': uv.isMain,
                'permissions': {
                    'allAccess': uv.allAccess,
                    'liveTracking': uv.liveTracking,
                    'history': uv.history,
                    'report': uv.report,
                    'vehicleProfile': uv.vehicleProfile,
                    'events': uv.events,
                    'geofence': uv.geofence,
                    'edit': uv.edit,
                    'shareTracking': uv.shareTracking,
                    'notification': uv.notification
                }
            })
        
        print(f"DEBUG: Returning vehicle data for IMEI: {vehicle.imei}, Name: {vehicle.name}, VehicleNo: {vehicle.vehicleNo}")
        
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
            'is_active': vehicle.is_active,
            'expireDate': vehicle.expireDate.isoformat() if vehicle.expireDate else None,
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
            'userVehicle': {
                'isMain': user_vehicle.isMain if user_vehicle else False,
                'permissions': {
                    'allAccess': user_vehicle.allAccess,
                    'liveTracking': user_vehicle.liveTracking,
                    'history': user_vehicle.history,
                    'report': user_vehicle.report,
                    'vehicleProfile': user_vehicle.vehicleProfile,
                    'events': user_vehicle.events,
                    'geofence': user_vehicle.geofence,
                    'edit': user_vehicle.edit,
                    'shareTracking': user_vehicle.shareTracking,
                    'notification': user_vehicle.notification
                } if user_vehicle else {}
            } if user_vehicle else None,
            'users': users_with_access,
            'todayKm': today_km,
            'latestStatus': latest_status,
            'latestLocation': latest_location
        }
        
        return success_response(vehicle_data, 'Vehicle retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def create_vehicle(request):
    """
    Create new vehicle with user-vehicle relationship
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['imei', 'name', 'vehicleNo', 'vehicleType']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['is_valid']:
            return error_response(validation_result['message'], HTTP_STATUS['BAD_REQUEST'])
        
        # Validate IMEI format
        if not validate_imei(data['imei']):
            return error_response('IMEI must be exactly 15 digits', HTTP_STATUS['BAD_REQUEST'])
        
        # Check if device IMEI exists
        try:
            device = Device.objects.get(imei=data['imei'])
        except Device.DoesNotExist:
            return error_response('Device with this IMEI does not exist. Please create the device first.', HTTP_STATUS['BAD_REQUEST'])
        
        # Check if vehicle with this IMEI already exists
        if Vehicle.objects.filter(imei=data['imei']).exists():
            return error_response('Vehicle with this IMEI already exists', HTTP_STATUS['BAD_REQUEST'])
        
        # Create vehicle
        with transaction.atomic():
            # Handle expireDate - set to one year from now if not provided
            expire_date = None
            if 'expireDate' in data and data['expireDate']:
                try:
                    from datetime import datetime
                    expire_date = datetime.fromisoformat(data['expireDate'].replace('Z', '+00:00'))
                except ValueError:
                    try:
                        expire_date = datetime.strptime(data['expireDate'], '%Y-%m-%d')
                    except ValueError:
                        pass  # Will use default one year from now
            else:
                # Set to one year from creation date if not provided
                from datetime import datetime, timedelta
                expire_date = datetime.now() + timedelta(days=365)
            
            vehicle = Vehicle.objects.create(
                imei=data['imei'],
                name=data['name'],
                vehicleNo=data['vehicleNo'],
                vehicleType=data['vehicleType'],
                device=device,
                odometer=data.get('odometer', 0),
                mileage=data.get('mileage', 0),
                minimumFuel=data.get('minimumFuel', 0),
                speedLimit=data.get('speedLimit', 60),
                expireDate=expire_date,
                is_active=data.get('is_active', True)
            )
            
            # Create user-vehicle relationship
            UserVehicle.objects.create(
                vehicle=vehicle,
                user=user,
                isMain=True,
                allAccess=True,  # Give full access to the creator
                liveTracking=True,
                history=True,
                report=True,
                vehicleProfile=True,
                events=True,
                geofence=True,
                edit=True,
                shareTracking=True,
                notification=True
            )
        
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
            'createdAt': vehicle.createdAt.isoformat() if vehicle.createdAt else None,
            'updatedAt': vehicle.updatedAt.isoformat() if vehicle.updatedAt else None
        }
        
        return success_response(vehicle_data, 'Vehicle created successfully', HTTP_STATUS['CREATED'])
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS['BAD_REQUEST'])
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["PUT"])
@require_auth
def update_vehicle(request, imei):
    """
    Update vehicle with role-based access
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        # Get vehicle with access check
        user_group = user.groups.first()
        if user_group and user_group.name == 'Super Admin':
            vehicle = Vehicle.objects.select_related('device').filter(imei=imei).first()
        else:
            vehicle = Vehicle.objects.filter(
                imei=imei,
                userVehicles__user=user
            ).select_related('device').first()
        
        if not vehicle:
            return error_response('Vehicle not found or access denied', HTTP_STATUS['NOT_FOUND'])
        
        # Only check for device existence and vehicle duplicates if IMEI is being changed
        if 'imei' in data and data['imei'] != imei:
            # Check if device exists
            try:
                device = Device.objects.get(imei=data['imei'])
            except Device.DoesNotExist:
                return error_response('Device with this IMEI does not exist', HTTP_STATUS['BAD_REQUEST'])
            
            # Check if another vehicle with the new IMEI already exists
            if Vehicle.objects.filter(imei=data['imei']).exclude(id=vehicle.id).exists():
                return error_response('Vehicle with this IMEI already exists', HTTP_STATUS['BAD_REQUEST'])
        
        # Update vehicle
        with transaction.atomic():
            if 'imei' in data:
                vehicle.imei = data['imei']
            if 'name' in data:
                vehicle.name = data['name']
            if 'vehicleNo' in data:
                vehicle.vehicleNo = data['vehicleNo']
            if 'vehicleType' in data:
                vehicle.vehicleType = data['vehicleType']
            if 'odometer' in data:
                vehicle.odometer = data['odometer']
            if 'mileage' in data:
                vehicle.mileage = data['mileage']
            if 'minimumFuel' in data:
                vehicle.minimumFuel = data['minimumFuel']
            if 'speedLimit' in data:
                vehicle.speedLimit = data['speedLimit']
            if 'expireDate' in data:
                if data['expireDate']:
                    # Parse the date string and convert to datetime
                    from datetime import datetime
                    try:
                        vehicle.expireDate = datetime.fromisoformat(data['expireDate'].replace('Z', '+00:00'))
                    except ValueError:
                        # If parsing fails, try alternative format
                        try:
                            vehicle.expireDate = datetime.strptime(data['expireDate'], '%Y-%m-%d')
                        except ValueError:
                            pass  # Keep existing value if parsing fails
                else:
                    vehicle.expireDate = None
            if 'status' in data:
                vehicle.status = data['status']
            if 'is_active' in data:
                vehicle.is_active = data['is_active']
            
            vehicle.save()
        
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
            'createdAt': vehicle.createdAt.isoformat() if vehicle.createdAt else None,
            'updatedAt': vehicle.updatedAt.isoformat() if vehicle.updatedAt else None
        }
        
        return success_response(vehicle_data, 'Vehicle updated successfully')
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS['BAD_REQUEST'])
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["DELETE"])
@require_auth
@require_role(['Super Admin'])
def delete_vehicle(request, imei):
    """
    Delete vehicle (only Super Admin)
    """
    try:
        # Get vehicle
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Delete vehicle and related data
        with transaction.atomic():
            # Delete user-vehicle relationships
            UserVehicle.objects.filter(vehicle=vehicle).delete()
            
            # Delete geofence-vehicle relationships (you'll need to implement this)
            # GeofenceVehicle.objects.filter(vehicle=vehicle).delete()
            
            # Delete ALL location data with this IMEI (you'll need to implement this)
            # Location.objects.filter(imei=imei).delete()
            
            # Delete ALL status data with this IMEI (you'll need to implement this)
            # Status.objects.filter(imei=imei).delete()
            
            # Delete the vehicle record itself
            vehicle.delete()
        
        return success_response(None, 'Vehicle deleted successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def assign_vehicle_access_to_user(request):
    """
    Assign vehicle access to user
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['imei', 'userPhone', 'permissions']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['is_valid']:
            return error_response(validation_result['message'], HTTP_STATUS['BAD_REQUEST'])
        
        imei = data['imei']
        user_phone = data['userPhone']
        permissions = data['permissions']
        
        # Check if target user exists
        try:
            target_user = User.objects.get(phone=user_phone)
        except User.DoesNotExist:
            return error_response('User not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check if user has permission to assign access
        user_group = user.groups.first()
        if not user_group or user_group.name != 'Super Admin':
            try:
                main_user_vehicle = UserVehicle.objects.get(
                    vehicle__imei=imei,
                    user=user,
                    isMain=True
                )
            except UserVehicle.DoesNotExist:
                return error_response('Access denied. Only main user or Super Admin can assign access', HTTP_STATUS['FORBIDDEN'])
        
        # Check if vehicle exists
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check if access is already assigned
        if UserVehicle.objects.filter(vehicle=vehicle, user=target_user).exists():
            return error_response('Vehicle access is already assigned to this user', HTTP_STATUS['BAD_REQUEST'])
        
        # Assign vehicle access to user
        user_vehicle = UserVehicle.objects.create(
            vehicle=vehicle,
            user=target_user,
            isMain=False,
            allAccess=permissions.get('allAccess', False),
            liveTracking=permissions.get('liveTracking', False),
            history=permissions.get('history', False),
            report=permissions.get('report', False),
            vehicleProfile=permissions.get('vehicleProfile', False),
            events=permissions.get('events', False),
            geofence=permissions.get('geofence', False),
            edit=permissions.get('edit', False),
            shareTracking=permissions.get('shareTracking', False),
            notification=permissions.get('notification', True)
        )
        
        assignment_data = {
            'id': user_vehicle.id,
            'vehicleId': vehicle.id,
            'userId': target_user.id,
            'isMain': user_vehicle.isMain,
            'permissions': {
                'allAccess': user_vehicle.allAccess,
                'liveTracking': user_vehicle.liveTracking,
                'history': user_vehicle.history,
                'report': user_vehicle.report,
                'vehicleProfile': user_vehicle.vehicleProfile,
                'events': user_vehicle.events,
                'geofence': user_vehicle.geofence,
                'edit': user_vehicle.edit,
                'shareTracking': user_vehicle.shareTracking,
                'notification': user_vehicle.notification
            },
            'createdAt': user_vehicle.createdAt.isoformat() if user_vehicle.createdAt else None
        }
        
        return success_response(assignment_data, 'Vehicle access assigned successfully')
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS['BAD_REQUEST'])
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_vehicles_for_access_assignment(request):
    """
    Get vehicles for access assignment
    """
    try:
        user = request.user
        
        # Get vehicles based on user role
        user_group = user.groups.first()
        if user_group and user_group.name == 'Super Admin':
            vehicles = Vehicle.objects.all()
        else:
            # Get vehicles where user is main user
            vehicles = Vehicle.objects.filter(
                userVehicles__user=user,
                userVehicles__isMain=True
            ).distinct()
        
        vehicles_data = []
        for vehicle in vehicles:
            vehicles_data.append({
                'id': vehicle.id,
                'imei': vehicle.imei,
                'name': vehicle.name,
                'vehicleNo': vehicle.vehicleNo,
                'vehicleType': vehicle.vehicleType
            })
        
        return success_response(vehicles_data, 'Vehicles for access assignment retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_vehicle_access_assignments(request, imei):
    """
    Get vehicle access assignments
    """
    try:
        user = request.user
        
        if not imei:
            return error_response('IMEI is required', HTTP_STATUS['BAD_REQUEST'])
        
        # Check if user has access to this vehicle
        user_group = user.groups.first()
        if not user_group or user_group.name != 'Super Admin':
            try:
                UserVehicle.objects.get(
                    vehicle__imei=imei,
                    user=user,
                    isMain=True
                )
            except UserVehicle.DoesNotExist:
                return error_response('Access denied', HTTP_STATUS['FORBIDDEN'])
        
        # Get vehicle access assignments
        user_vehicles = UserVehicle.objects.filter(
            vehicle__imei=imei
        ).select_related('user')
        
        assignments_data = []
        for uv in user_vehicles:
            assignments_data.append({
                'id': uv.id,
                'userId': uv.user.id,
                'userName': uv.user.name,
                'userPhone': uv.user.phone,
                'userRole': uv.user.groups.first().name if uv.user.groups.exists() else 'User',
                'isMain': uv.isMain,
                'permissions': {
                    'allAccess': uv.allAccess,
                    'liveTracking': uv.liveTracking,
                    'history': uv.history,
                    'report': uv.report,
                    'vehicleProfile': uv.vehicleProfile,
                    'events': uv.events,
                    'geofence': uv.geofence,
                    'edit': uv.edit,
                    'shareTracking': uv.shareTracking,
                    'notification': uv.notification
                },
                'createdAt': uv.createdAt.isoformat() if uv.createdAt else None
            })
        
        return success_response(assignments_data, 'Vehicle access assignments retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["PUT"])
@require_auth
def update_vehicle_access(request):
    """
    Update vehicle access
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['imei', 'userId', 'permissions']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['is_valid']:
            return error_response(validation_result['message'], HTTP_STATUS['BAD_REQUEST'])
        
        imei = data['imei']
        user_id = data['userId']
        permissions = data['permissions']
        
        # Check if user has permission to update access
        user_group = user.groups.first()
        if not user_group or user_group.name != 'Super Admin':
            try:
                main_user_vehicle = UserVehicle.objects.get(
                    vehicle__imei=imei,
                    user=user,
                    isMain=True
                )
            except UserVehicle.DoesNotExist:
                return error_response('Access denied. Only main user or Super Admin can update access', HTTP_STATUS['FORBIDDEN'])
        
        # Check if vehicle exists
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Update vehicle access
        try:
            user_vehicle = UserVehicle.objects.get(vehicle=vehicle, user_id=user_id)
            user_vehicle.allAccess = permissions.get('allAccess', False)
            user_vehicle.liveTracking = permissions.get('liveTracking', False)
            user_vehicle.history = permissions.get('history', False)
            user_vehicle.report = permissions.get('report', False)
            user_vehicle.vehicleProfile = permissions.get('vehicleProfile', False)
            user_vehicle.events = permissions.get('events', False)
            user_vehicle.geofence = permissions.get('geofence', False)
            user_vehicle.edit = permissions.get('edit', False)
            user_vehicle.shareTracking = permissions.get('shareTracking', False)
            user_vehicle.notification = permissions.get('notification', True)
            user_vehicle.save()
        except UserVehicle.DoesNotExist:
            return error_response('Vehicle access assignment not found', HTTP_STATUS['NOT_FOUND'])
        
        assignment_data = {
            'id': user_vehicle.id,
            'vehicleId': vehicle.id,
            'userId': user_vehicle.user.id,
            'isMain': user_vehicle.isMain,
            'permissions': {
                'allAccess': user_vehicle.allAccess,
                'liveTracking': user_vehicle.liveTracking,
                'history': user_vehicle.history,
                'report': user_vehicle.report,
                'vehicleProfile': user_vehicle.vehicleProfile,
                'events': user_vehicle.events,
                'geofence': user_vehicle.geofence,
                'edit': user_vehicle.edit,
                'shareTracking': user_vehicle.shareTracking,
                'notification': user_vehicle.notification
            },
            'createdAt': user_vehicle.createdAt.isoformat() if user_vehicle.createdAt else None
        }
        
        return success_response(assignment_data, 'Vehicle access updated successfully')
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS['BAD_REQUEST'])
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["DELETE"])
@require_auth
def remove_vehicle_access(request):
    """
    Remove vehicle access
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['imei', 'userId']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['is_valid']:
            return error_response(validation_result['message'], HTTP_STATUS['BAD_REQUEST'])
        
        imei = data['imei']
        user_id = data['userId']
        
        # Check if user has permission to remove access
        user_group = user.groups.first()
        if not user_group or user_group.name != 'Super Admin':
            try:
                main_user_vehicle = UserVehicle.objects.get(
                    vehicle__imei=imei,
                    user=user,
                    isMain=True
                )
            except UserVehicle.DoesNotExist:
                return error_response('Access denied. Only main user or Super Admin can remove access', HTTP_STATUS['FORBIDDEN'])
        
        # Check if vehicle exists
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Remove vehicle access
        try:
            user_vehicle = UserVehicle.objects.get(vehicle=vehicle, user_id=user_id)
            user_vehicle.delete()
        except UserVehicle.DoesNotExist:
            return error_response('Vehicle access assignment not found', HTTP_STATUS['NOT_FOUND'])
        
        return success_response(None, 'Vehicle access removed successfully')
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS['BAD_REQUEST'])
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_vehicles_with_access_paginated(request):
    """
    Get paginated vehicles with access information for vehicle access management
    """
    try:
        user = request.user
        
        # Get page number from query parameters, default to 1
        page_number = int(request.GET.get('page', 1))
        page_size = 25  # Fixed page size as requested
        
        # Get vehicles based on user role
        user_group = user.groups.first()
        if user_group and user_group.name == 'Super Admin':
            vehicles = Vehicle.objects.select_related('device').prefetch_related('userVehicles__user').all()
        else:
            # Get vehicles where user has access
            vehicles = Vehicle.objects.filter(
                Q(userVehicles__user=user) |  # Direct vehicle access
                Q(device__userDevices__user=user)  # Device access
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
            user_vehicles_data = []
            for user_vehicle in vehicle.userVehicles.all():
                user_vehicles_data.append({
                    'id': user_vehicle.id,
                    'userId': user_vehicle.user.id,
                    'userName': user_vehicle.user.name,
                    'userPhone': user_vehicle.user.phone,
                    'isMain': user_vehicle.isMain,
                    'allAccess': user_vehicle.allAccess,
                    'liveTracking': user_vehicle.liveTracking,
                    'history': user_vehicle.history,
                    'report': user_vehicle.report,
                    'vehicleProfile': user_vehicle.vehicleProfile,
                    'events': user_vehicle.events,
                    'geofence': user_vehicle.geofence,
                    'edit': user_vehicle.edit,
                    'shareTracking': user_vehicle.shareTracking,
                    'notification': user_vehicle.notification,
                    'relay': user_vehicle.relay,
                    'createdAt': user_vehicle.createdAt.isoformat() if user_vehicle.createdAt else None,
                    'user': {
                        'id': user_vehicle.user.id,
                        'name': user_vehicle.user.name,
                        'phone': user_vehicle.user.phone,
                        'email': user_vehicle.user.email,
                        'role': user_vehicle.user.groups.first().name if user_vehicle.user.groups.exists() else 'User'
                    }
                })
            
            vehicle_data = {
                'id': vehicle.id,
                'imei': vehicle.imei,
                'name': vehicle.name,
                'vehicleNo': vehicle.vehicleNo,
                'vehicleType': vehicle.vehicleType,
                'device': {
                    'id': vehicle.device.id if vehicle.device else None,
                    'imei': vehicle.device.imei if vehicle.device else None,
                    'phone': vehicle.device.phone if vehicle.device else None,
                    'status': vehicle.device.status if vehicle.device else None
                } if vehicle.device else None,
                'userVehicles': user_vehicles_data,
                'createdAt': vehicle.createdAt.isoformat() if vehicle.createdAt else None,
                'updatedAt': vehicle.updatedAt.isoformat() if vehicle.updatedAt else None
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
        
        return success_response(response_data, 'Paginated vehicles with access retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def search_vehicles_with_access(request):
    """
    Search vehicles with access information by vehicle details and user details
    """
    try:
        user = request.user
        
        # Get search query and page number from query parameters
        search_query = request.GET.get('q', '').strip()
        page_number = int(request.GET.get('page', 1))
        page_size = 25  # Fixed page size as requested
        
        if not search_query:
            return error_response('Search query is required', HTTP_STATUS['BAD_REQUEST'])
        
        # Build search filter
        search_filter = (
            Q(name__icontains=search_query) |
            Q(vehicleNo__icontains=search_query) |
            Q(imei__icontains=search_query) |
            Q(vehicleType__icontains=search_query) |
            Q(userVehicles__user__name__icontains=search_query) |
            Q(userVehicles__user__phone__icontains=search_query) |
            Q(device__phone__icontains=search_query)
        )
        
        # Get vehicles based on user role and apply search
        user_group = user.groups.first()
        if user_group and user_group.name == 'Super Admin':
            # Super Admin can see all vehicles that match search
            vehicles = Vehicle.objects.filter(search_filter).select_related('device').prefetch_related('userVehicles__user').distinct()
        else:
            # For regular users, find vehicles that match search AND user has access to
            vehicles = Vehicle.objects.filter(
                Q(search_filter) & (
                    Q(userVehicles__user=user) |  # Direct vehicle access
                    Q(device__userDevices__user=user)  # Device access
                )
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
            user_vehicles_data = []
            for user_vehicle in vehicle.userVehicles.all():
                user_vehicles_data.append({
                    'id': user_vehicle.id,
                    'userId': user_vehicle.user.id,
                    'userName': user_vehicle.user.name,
                    'userPhone': user_vehicle.user.phone,
                    'isMain': user_vehicle.isMain,
                    'allAccess': user_vehicle.allAccess,
                    'liveTracking': user_vehicle.liveTracking,
                    'history': user_vehicle.history,
                    'report': user_vehicle.report,
                    'vehicleProfile': user_vehicle.vehicleProfile,
                    'events': user_vehicle.events,
                    'geofence': user_vehicle.geofence,
                    'edit': user_vehicle.edit,
                    'shareTracking': user_vehicle.shareTracking,
                    'notification': user_vehicle.notification,
                    'relay': user_vehicle.relay,
                    'createdAt': user_vehicle.createdAt.isoformat() if user_vehicle.createdAt else None,
                    'user': {
                        'id': user_vehicle.user.id,
                        'name': user_vehicle.user.name,
                        'phone': user_vehicle.user.phone,
                        'email': user_vehicle.user.email,
                        'role': user_vehicle.user.groups.first().name if user_vehicle.user.groups.exists() else 'User'
                    }
                })
            
            vehicle_data = {
                'id': vehicle.id,
                'imei': vehicle.imei,
                'name': vehicle.name,
                'vehicleNo': vehicle.vehicleNo,
                'vehicleType': vehicle.vehicleType,
                'device': {
                    'id': vehicle.device.id if vehicle.device else None,
                    'imei': vehicle.device.imei if vehicle.device else None,
                    'phone': vehicle.device.phone if vehicle.device else None,
                    'status': vehicle.device.status if vehicle.device else None
                } if vehicle.device else None,
                'userVehicles': user_vehicles_data,
                'createdAt': vehicle.createdAt.isoformat() if vehicle.createdAt else None,
                'updatedAt': vehicle.updatedAt.isoformat() if vehicle.updatedAt else None
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
        
        return success_response(response_data, f'Found {paginator.count} vehicles matching "{search_query}"')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_vehicles_paginated(request):
    """
    Get paginated vehicles with detailed data for table display (includes device, user, recharge info)
    """
    try:
        user = request.user
        
        # Get page number from query parameters, default to 1
        page_number = int(request.GET.get('page', 1))
        page_size = 25  # Fixed page size as requested
        
        # Get vehicles based on user role
        user_group = user.groups.first()
        if user_group and user_group.name == 'Super Admin':
            vehicles = Vehicle.objects.select_related('device').prefetch_related('userVehicles__user').all()
        else:
            # Get vehicles where user has access
            vehicles = Vehicle.objects.filter(
                Q(userVehicles__user=user) |  # Direct vehicle access
                Q(device__userDevices__user=user)  # Device access
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
                        'createdAt': uv.createdAt.isoformat(),
                        'updatedAt': uv.createdAt.isoformat()
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
                    'createdAt': latest_status_obj.createdAt.isoformat()
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
                    'createdAt': latest_location_obj.createdAt.isoformat()
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
                'todayKm': today_km
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
        
        return success_response(response_data, 'Paginated vehicles retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def search_vehicles(request):
    """
    Search vehicles with multiple fields: vehicle name, vehicle no, device imei, device phone, device sim, related users (name and phone), device-related users (name and phone)
    Supports pagination with page parameter
    """
    try:
        user = request.user
        search_query = request.GET.get('q', '').strip()
        page_number = int(request.GET.get('page', 1))
        page_size = 25  # Fixed page size
        
        if not search_query:
            return error_response('Search query is required', HTTP_STATUS['BAD_REQUEST'])
        
        # Build search filters first
        search_filter = Q()
        
        # Search in vehicle fields
        search_filter |= Q(name__icontains=search_query)
        search_filter |= Q(vehicleNo__icontains=search_query)
        search_filter |= Q(imei__icontains=search_query)
        
        # Search in device fields
        search_filter |= Q(device__imei__icontains=search_query)
        search_filter |= Q(device__phone__icontains=search_query)
        search_filter |= Q(device__sim__icontains=search_query)
        
        # Search in related users (name and phone)
        search_filter |= Q(userVehicles__user__name__icontains=search_query)
        search_filter |= Q(userVehicles__user__phone__icontains=search_query)
        
        # Search in device-related users (name and phone)
        search_filter |= Q(device__userDevices__user__name__icontains=search_query)
        search_filter |= Q(device__userDevices__user__phone__icontains=search_query)
        
        # Get vehicles based on user role and apply search
        user_group = user.groups.first()
        if user_group and user_group.name == 'Super Admin':
            # Super Admin can see all vehicles that match search
            vehicles = Vehicle.objects.filter(search_filter).select_related('device').prefetch_related('userVehicles__user').distinct()
        else:
            # For regular users, find vehicles that match search AND user has access to
            # OR vehicles that match search through device-related users
            vehicles = Vehicle.objects.filter(
                Q(search_filter) & (
                    Q(userVehicles__user=user) |  # Direct vehicle access
                    Q(device__userDevices__user=user)  # Device access
                )
            ).select_related('device').prefetch_related('userVehicles__user').distinct()
            
            # Also include vehicles that match search through device-related users
            # even if current user doesn't have direct access
            additional_vehicles = Vehicle.objects.filter(
                Q(device__userDevices__user__name__icontains=search_query) |
                Q(device__userDevices__user__phone__icontains=search_query)
            ).exclude(
                Q(userVehicles__user=user) |  # Exclude vehicles user already has access to
                Q(device__userDevices__user=user)
            ).select_related('device').prefetch_related('userVehicles__user').distinct()
            
            print(f"DEBUG: Initial vehicles count: {vehicles.count()}")
            print(f"DEBUG: Additional vehicles count: {additional_vehicles.count()}")
            print(f"DEBUG: Search query: {search_query}")
            
            # Combine the results
            vehicles = vehicles.union(additional_vehicles)
            print(f"DEBUG: Final vehicles count: {vehicles.count()}")
        
        # Create paginator
        paginator = Paginator(vehicles, page_size)
        
        # Get the requested page
        try:
            page_obj = paginator.get_page(page_number)
        except:
            return error_response('Invalid page number', HTTP_STATUS['BAD_REQUEST'])
        
        vehicles_data = []
        for vehicle in page_obj:
            # Get all users with access to this vehicle
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
                        'createdAt': uv.createdAt.isoformat(),
                        'updatedAt': uv.createdAt.isoformat()
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
                    'createdAt': latest_status_obj.createdAt.isoformat()
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
                    'createdAt': latest_location_obj.createdAt.isoformat()
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
                'mainCustomer': main_customer,
                'latestRecharge': latest_recharge,
                'latestStatus': latest_status,
                'latestLocation': latest_location,
                'todayKm': today_km
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
        
        return success_response(response_data, f'Found {paginator.count} vehicles matching "{search_query}"')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["PUT"])
@require_auth
def activate_vehicle(request, imei):
    """
    Activate a vehicle
    """
    try:
        user = request.user
        
        # Get vehicle
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # # Check permissions
        # user_vehicle = vehicle.userVehicles.filter(user=user).first()
        # if not user_vehicle or not user_vehicle.edit:
        #     return error_response('You do not have permission to edit this vehicle', HTTP_STATUS['FORBIDDEN'])
        
        # Activate vehicle
        vehicle.is_active = True
        vehicle.save()
        
        return success_response({
            'id': vehicle.id,
            'imei': vehicle.imei,
            'name': vehicle.name,
            'vehicleNo': vehicle.vehicleNo,
            'is_active': vehicle.is_active
        }, 'Vehicle activated successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["PUT"])
@require_auth
def deactivate_vehicle(request, imei):
    """
    Deactivate a vehicle
    """
    try:
        user = request.user
        
        # Get vehicle
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check permissions
        # user_vehicle = vehicle.userVehicles.filter(user=user).first()
        # if not user_vehicle or not user_vehicle.edit:
        #     return error_response('You do not have permission to edit this vehicle', HTTP_STATUS['FORBIDDEN'])
        
        # Deactivate vehicle
        vehicle.is_active = False
        vehicle.save()
        
        return success_response({
            'id': vehicle.id,
            'imei': vehicle.imei,
            'name': vehicle.name,
            'vehicleNo': vehicle.vehicleNo,
            'is_active': vehicle.is_active
        }, 'Vehicle deactivated successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_light_vehicles(request):
    """
    Get light vehicle data for dropdown lists (playback and history)
    Returns only essential fields: id, imei, name, vehicleNo, vehicleType
    """
    try:
        user = request.user
        
        # Get vehicles based on user role
        user_group = user.groups.first()
        if user_group and user_group.name == 'Super Admin':
            vehicles = Vehicle.objects.filter(is_active=True).values(
                'id', 'imei', 'name', 'vehicleNo', 'vehicleType', 'is_active'
            ).order_by('name')
        else:
            # Get vehicles where user has access
            vehicles = Vehicle.objects.filter(
                Q(userVehicles__user=user) |  # Direct vehicle access
                Q(device__userDevices__user=user)  # Device access
            ).filter(is_active=True).values(
                'id', 'imei', 'name', 'vehicleNo', 'vehicleType', 'is_active'
            ).distinct().order_by('name')
        
        vehicles_list = list(vehicles)
        
        return success_response(
            data=vehicles_list,
            message='Light vehicles retrieved successfully'
        )
    except Exception as e:
        return handle_api_exception(e)