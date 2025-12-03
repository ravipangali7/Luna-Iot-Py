"""
Garbage Vehicle Views
Handles garbage vehicle management endpoints
"""
from rest_framework.decorators import api_view
from django.core.paginator import Paginator
from django.db.models import Q
from garbage.models import GarbageVehicle, GarbageVehicleSubscription
from garbage.serializers import (
    GarbageVehicleSerializer,
    GarbageVehicleCreateSerializer,
    GarbageVehicleListSerializer,
    GarbageVehicleSubscriptionSerializer,
    GarbageVehicleSubscriptionCreateSerializer
)
from fleet.models import Vehicle
from shared_utils.constants import VehicleType
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError
from core.models import Module, InstituteModule
from device.models import Location


def require_garbage_module_access(model_class=None, id_param_name='id'):
    """
    Decorator to require Super Admin role OR institute module access for garbage operations
    
    Args:
        model_class: Optional model class to fetch record for PUT/DELETE operations
                    Should have 'institute' field (ForeignKey)
        id_param_name: Name of the URL parameter containing the record ID (default: 'id')
    
    For create operations (POST): extracts institute_id from request.data['institute']
    For update/delete operations (PUT/DELETE): fetches record using model_class and extracts institute_id
    """
    def decorator(view_func):
        from functools import wraps
        from api_common.utils.response_utils import error_response
        
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return error_response(
                    message='Authentication required',
                    status_code=401
                )
            
            # Check if user is Super Admin - always allow
            user_groups = request.user.groups.all()
            user_role_names = [group.name for group in user_groups]
            is_super_admin = 'Super Admin' in user_role_names
            
            if is_super_admin:
                return view_func(request, *args, **kwargs)
            
            # For non-Super Admin users, check institute module access
            try:
                # Get the garbage module
                garbage_module = Module.objects.get(slug='garbage')
            except Module.DoesNotExist:
                return error_response(
                    message='Garbage module not found',
                    status_code=500
                )
            
            # Get institute_id(s) based on HTTP method
            institute_ids = []
            
            if request.method == 'POST':
                # For create operations, get institute_id from request.data
                institute_id = request.data.get('institute')
                if institute_id:
                    if isinstance(institute_id, dict):
                        institute_id = institute_id.get('id') or institute_id.get('pk')
                    elif hasattr(institute_id, 'id'):
                        institute_id = institute_id.id
                    if institute_id:
                        institute_ids = [institute_id]
            elif request.method in ['PUT', 'DELETE'] and model_class:
                # For update/delete operations, get record and extract institute_id
                record_id = kwargs.get(id_param_name) or kwargs.get('vehicle_id')
                if record_id:
                    try:
                        record = model_class.objects.get(id=record_id)
                        
                        # Check if record has direct institute field
                        if hasattr(record, 'institute'):
                            institute = record.institute
                            if institute:
                                institute_ids = [institute.id if hasattr(institute, 'id') else institute]
                    except model_class.DoesNotExist:
                        # Record doesn't exist - let the view handle the 404
                        pass
            
            # Check if user has access to any of the institutes
            if institute_ids:
                has_access = InstituteModule.objects.filter(
                    module=garbage_module,
                    institute_id__in=institute_ids,
                    users=request.user
                ).exists()
                
                if not has_access:
                    return error_response(
                        message='Access denied. Insufficient permissions',
                        status_code=403
                    )
            else:
                # If no institute_id found and not Super Admin, deny access
                return error_response(
                    message='Access denied. Insufficient permissions',
                    status_code=403
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


@api_view(['GET'])
@require_auth
@api_response
def get_garbage_vehicle_vehicles(request):
    """Get vehicles available for garbage vehicle assignment with role-based access control"""
    try:
        user = request.user
        
        # Filter vehicles where vehicleType = 'Garbage'
        base_query = Vehicle.objects.filter(
            vehicleType=VehicleType.GARBAGE,
            is_active=True
        ).select_related('device').prefetch_related('userVehicles__user')
        
        # Get vehicles based on user role
        user_group = user.groups.first()
        if user_group and user_group.name == 'Super Admin':
            # Super Admin: Return all garbage vehicles
            vehicles = base_query.all()
        else:
            # Other roles: Return only vehicles where user has access
            vehicles = base_query.filter(
                Q(userVehicles__user=user) |  # Direct vehicle access
                Q(device__userDevices__user=user)  # Device access
            ).distinct()
        
        # Order by name for consistency
        vehicles = vehicles.order_by('name')
        
        # Return minimal vehicle data suitable for dropdowns
        vehicles_data = []
        for vehicle in vehicles:
            vehicles_data.append({
                'id': vehicle.id,
                'imei': vehicle.imei,
                'name': vehicle.name,
                'vehicleNo': vehicle.vehicleNo,
                'vehicleType': vehicle.vehicleType,
                'is_active': vehicle.is_active
            })
        
        return success_response(
            data=vehicles_data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Vehicles retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_all_garbage_vehicles(request):
    """Get all garbage vehicles with pagination and filtering"""
    try:
        search_query = request.GET.get('search', '').strip()
        institute_filter = request.GET.get('institute_id', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        garbage_vehicles = GarbageVehicle.objects.select_related('institute', 'vehicle').all()
        
        if search_query:
            garbage_vehicles = garbage_vehicles.filter(
                Q(institute__name__icontains=search_query) |
                Q(vehicle__name__icontains=search_query) |
                Q(vehicle__vehicleNo__icontains=search_query)
            )
        
        if institute_filter:
            garbage_vehicles = garbage_vehicles.filter(institute_id=institute_filter)
        
        garbage_vehicles = garbage_vehicles.order_by('-created_at')
        
        paginator = Paginator(garbage_vehicles, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = GarbageVehicleListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Garbage vehicles retrieved successfully'),
            data={
                'garbage_vehicles': serializer.data,
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
def get_garbage_vehicle_by_id(request, vehicle_id):
    """Get garbage vehicle by ID"""
    try:
        try:
            garbage_vehicle = GarbageVehicle.objects.select_related('institute', 'vehicle').get(id=vehicle_id)
        except GarbageVehicle.DoesNotExist:
            raise NotFoundError("Garbage vehicle not found")
        
        serializer = GarbageVehicleSerializer(garbage_vehicle)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Garbage vehicle retrieved successfully')
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
def get_garbage_vehicles_by_institute(request, institute_id):
    """Get garbage vehicles by institute"""
    try:
        garbage_vehicles = GarbageVehicle.objects.select_related('institute', 'vehicle').filter(
            institute_id=institute_id
        ).order_by('-created_at')
        
        serializer = GarbageVehicleListSerializer(garbage_vehicles, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Garbage vehicles retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_garbage_module_access()
@api_response
def create_garbage_vehicle(request):
    """Create new garbage vehicle"""
    try:
        serializer = GarbageVehicleCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            garbage_vehicle = serializer.save()
            response_serializer = GarbageVehicleSerializer(garbage_vehicle)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Garbage vehicle created successfully'),
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
@require_garbage_module_access(model_class=GarbageVehicle, id_param_name='vehicle_id')
@api_response
def update_garbage_vehicle(request, vehicle_id):
    """Update garbage vehicle"""
    try:
        try:
            garbage_vehicle = GarbageVehicle.objects.get(id=vehicle_id)
        except GarbageVehicle.DoesNotExist:
            raise NotFoundError("Garbage vehicle not found")
        
        serializer = GarbageVehicleCreateSerializer(garbage_vehicle, data=request.data)
        
        if serializer.is_valid():
            garbage_vehicle = serializer.save()
            response_serializer = GarbageVehicleSerializer(garbage_vehicle)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Garbage vehicle updated successfully')
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
@require_garbage_module_access(model_class=GarbageVehicle, id_param_name='vehicle_id')
@api_response
def delete_garbage_vehicle(request, vehicle_id):
    """Delete garbage vehicle"""
    try:
        try:
            garbage_vehicle = GarbageVehicle.objects.get(id=vehicle_id)
        except GarbageVehicle.DoesNotExist:
            raise NotFoundError("Garbage vehicle not found")
        
        vehicle_name = f"{garbage_vehicle.institute.name} - {garbage_vehicle.vehicle.name}"
        garbage_vehicle.delete()
        
        return success_response(
            data={'id': vehicle_id},
            message=f"Garbage vehicle '{vehicle_name}' deleted successfully"
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
def get_all_garbage_vehicles_with_locations(request):
    """
    Get all garbage institutes with their vehicles and latest locations
    Returns structured data for map display
    No role or InstituteModule access check - everyone can access vehicles they have permission to
    """
    try:
        user = request.user
        print(f"=== GARBAGE VEHICLES WITH LOCATIONS API ===")
        print(f"User: {user.name} (ID: {user.id})")
        print(f"User phone: {user.phone}")
        
        # Get all IMEIs for bulk location query
        all_imeis = set()
        institute_vehicle_map = {}
        
        # Get all garbage vehicles from all institutes (no access check - everyone can see all)
        garbage_vehicles = GarbageVehicle.objects.select_related(
            'vehicle', 'institute'
        ).order_by('-created_at')
        
        print(f"Total garbage vehicles: {garbage_vehicles.count()}")
        
        # Group by institute
        for gv in garbage_vehicles:
            institute = gv.institute
            institute_id = institute.id
            
            if institute_id not in institute_vehicle_map:
                institute_vehicle_map[institute_id] = {
                    'institute': institute,
                    'vehicles': []
                }
            
            institute_vehicle_map[institute_id]['vehicles'].append(gv.vehicle)
            all_imeis.add(gv.vehicle.imei)
            print(f"  Added vehicle {gv.vehicle.imei} ({gv.vehicle.name}) for institute {institute.name}")
        
        print(f"Total institutes in map: {len(institute_vehicle_map)}")
        print(f"Total IMEIs for location lookup: {len(all_imeis)}")
        
        # Get latest locations for all vehicles in one query
        locations_dict = {}
        if all_imeis:
            print(f"=== FETCHING LOCATIONS ===")
            # Get latest location for each IMEI
            for imei in all_imeis:
                latest_location = Location.objects.filter(
                    imei=imei
                ).order_by('-createdAt').first()
                
                if latest_location:
                    locations_dict[imei] = {
                        'id': latest_location.id,
                        'imei': latest_location.imei,
                        'latitude': float(latest_location.latitude),
                        'longitude': float(latest_location.longitude),
                        'speed': latest_location.speed,
                        'course': latest_location.course,
                        'satellite': latest_location.satellite,
                        'realTimeGps': latest_location.realTimeGps,
                        'createdAt': latest_location.createdAt.isoformat(),
                        'updatedAt': latest_location.updatedAt.isoformat()
                    }
                    print(f"  Location found for {imei}: {latest_location.latitude}, {latest_location.longitude}")
                else:
                    print(f"  No location found for {imei}")
        
        print(f"Total locations found: {len(locations_dict)}")
        
        # Structure response
        response_data = []
        print(f"=== STRUCTURING RESPONSE ===")
        for institute_id, data in institute_vehicle_map.items():
            institute = data['institute']
            vehicles_data = []
            
            print(f"Processing institute: {institute.name} (ID: {institute_id})")
            print(f"  Vehicles in institute: {len(data['vehicles'])}")
            
            for vehicle in data['vehicles']:
                # Get vehicle data
                vehicle_data = {
                    'id': vehicle.id,
                    'imei': vehicle.imei,
                    'name': vehicle.name,
                    'vehicleNo': vehicle.vehicleNo,
                    'vehicleType': vehicle.vehicleType,
                    'odometer': float(vehicle.odometer) if vehicle.odometer else None,
                    'mileage': float(vehicle.mileage) if vehicle.mileage else None,
                    'speedLimit': vehicle.speedLimit,
                    'minimumFuel': float(vehicle.minimumFuel) if vehicle.minimumFuel else None,
                    'is_active': vehicle.is_active,
                    'is_relay': vehicle.is_relay,
                }
                
                # Get location if available
                location = locations_dict.get(vehicle.imei)
                
                vehicles_data.append({
                    'vehicle': vehicle_data,
                    'location': location
                })
                print(f"    Vehicle {vehicle.imei} - Location: {'Yes' if location else 'No'}")
            
            # Only include institutes that have vehicles
            if vehicles_data:
                response_data.append({
                    'institute': {
                        'id': institute.id,
                        'name': institute.name,
                        'phone': institute.phone or '',
                        'address': institute.address or '',
                        'latitude': float(institute.latitude) if institute.latitude else None,
                        'longitude': float(institute.longitude) if institute.longitude else None,
                    },
                    'vehicles': vehicles_data
                })
                print(f"  Added institute {institute.name} with {len(vehicles_data)} vehicles to response")
        
        print(f"=== FINAL RESPONSE ===")
        print(f"Total institutes in response: {len(response_data)}")
        total_vehicles = sum(len(item['vehicles']) for item in response_data)
        print(f"Total vehicles in response: {total_vehicles}")
        
        return success_response(
            data=response_data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Garbage vehicles with locations retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_auth
@api_response
def subscribe_to_garbage_vehicle(request):
    """Subscribe to garbage vehicle notifications"""
    try:
        serializer = GarbageVehicleSubscriptionCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            subscription = serializer.save()
            response_serializer = GarbageVehicleSubscriptionSerializer(subscription)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Subscribed to garbage vehicle successfully'),
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


@api_view(['DELETE'])
@require_auth
@api_response
def unsubscribe_from_garbage_vehicle(request):
    """Unsubscribe from garbage vehicle notifications"""
    try:
        imei = request.data.get('imei')
        
        if not imei:
            return error_response(
                message='IMEI is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response(
                message='Vehicle not found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        try:
            subscription = GarbageVehicleSubscription.objects.get(user=request.user, vehicle=vehicle)
            subscription.delete()
            
            return success_response(
                data={'imei': imei},
                message='Unsubscribed from garbage vehicle successfully'
            )
        except GarbageVehicleSubscription.DoesNotExist:
            return error_response(
                message='Subscription not found',
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
def get_my_garbage_vehicle_subscriptions(request):
    """Get all garbage vehicle subscriptions for current user"""
    try:
        subscriptions = GarbageVehicleSubscription.objects.filter(
            user=request.user
        ).select_related('vehicle', 'user').order_by('-created_at')
        
        serializer = GarbageVehicleSubscriptionSerializer(subscriptions, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Subscriptions retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['PUT'])
@require_auth
@api_response
def update_garbage_vehicle_subscription_location(request, subscription_id):
    """Update subscription location"""
    try:
        try:
            subscription = GarbageVehicleSubscription.objects.get(id=subscription_id, user=request.user)
        except GarbageVehicleSubscription.DoesNotExist:
            raise NotFoundError("Subscription not found")
        
        serializer = GarbageVehicleSubscriptionCreateSerializer(
            subscription,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            subscription = serializer.save()
            response_serializer = GarbageVehicleSubscriptionSerializer(subscription)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Subscription location updated successfully')
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

