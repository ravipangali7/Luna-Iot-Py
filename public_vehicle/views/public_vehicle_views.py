"""
Public Vehicle Views
Handles public vehicle management endpoints
"""
from rest_framework.decorators import api_view
from django.core.paginator import Paginator
from django.db.models import Q
from public_vehicle.models import PublicVehicle, PublicVehicleImage
from public_vehicle.serializers import (
    PublicVehicleSerializer,
    PublicVehicleCreateSerializer,
    PublicVehicleListSerializer
)
from fleet.models import Vehicle
from shared_utils.constants import VehicleType
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth
from api_common.exceptions.api_exceptions import NotFoundError
from core.models import Module, InstituteModule


def require_public_vehicle_module_access(model_class=None, id_param_name='id'):
    """
    Decorator to require Super Admin role OR institute module access for public vehicle operations
    
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
                # Get the public-vehicle module
                public_vehicle_module = Module.objects.get(slug='public-vehicle')
            except Module.DoesNotExist:
                return error_response(
                    message='Public vehicle module not found',
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
            elif request.method == 'GET':
                # For GET operations, check URL parameters for institute_id
                institute_id = kwargs.get('institute_id')
                if not institute_id:
                    # Also check if there's a record ID and we need to get institute from it
                    record_id = kwargs.get(id_param_name) or kwargs.get('vehicle_id')
                    if record_id and model_class:
                        try:
                            record = model_class.objects.get(id=record_id)
                            if hasattr(record, 'institute'):
                                institute = record.institute
                                if institute:
                                    institute_ids = [institute.id if hasattr(institute, 'id') else institute]
                        except model_class.DoesNotExist:
                            pass
                else:
                    institute_ids = [institute_id]
            elif request.method in ['PUT', 'DELETE', 'PATCH'] and model_class:
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
                    module=public_vehicle_module,
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
def get_public_vehicle_vehicles(request):
    """Get vehicles available for public vehicle assignment with role-based access control"""
    try:
        user = request.user
        
        # Get all active vehicles (not filtered by type for public vehicles)
        base_query = Vehicle.objects.filter(
            is_active=True
        ).select_related('device').prefetch_related('userVehicles__user')
        
        # Get vehicles based on user role
        user_group = user.groups.first()
        if user_group and user_group.name == 'Super Admin':
            # Super Admin: Return all vehicles
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
def get_all_public_vehicles(request):
    """Get all public vehicles with pagination and filtering"""
    try:
        search_query = request.GET.get('search', '').strip()
        institute_filter = request.GET.get('institute_id', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        public_vehicles = PublicVehicle.objects.select_related('institute').prefetch_related('images').all()
        
        if search_query:
            public_vehicles = public_vehicles.filter(
                Q(institute__name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        if institute_filter:
            public_vehicles = public_vehicles.filter(institute_id=institute_filter)
        
        public_vehicles = public_vehicles.order_by('-created_at')
        
        paginator = Paginator(public_vehicles, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = PublicVehicleListSerializer(page_obj.object_list, many=True, context={'request': request})
        
        return success_response(
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Public vehicles retrieved successfully'),
            data={
                'public_vehicles': serializer.data,
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
@require_public_vehicle_module_access(model_class=PublicVehicle, id_param_name='vehicle_id')
@api_response
def get_public_vehicle_by_id(request, vehicle_id):
    """Get public vehicle by ID"""
    try:
        try:
            public_vehicle = PublicVehicle.objects.select_related('institute', 'vehicle').prefetch_related('images').get(id=vehicle_id)
        except PublicVehicle.DoesNotExist:
            raise NotFoundError("Public vehicle not found")
        
        serializer = PublicVehicleSerializer(public_vehicle, context={'request': request})
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Public vehicle retrieved successfully')
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
@require_public_vehicle_module_access()
@api_response
def get_public_vehicles_by_institute(request, institute_id):
    """Get public vehicles by institute"""
    try:
        public_vehicles = PublicVehicle.objects.select_related('institute', 'vehicle').prefetch_related('images').filter(
            institute_id=institute_id
        ).order_by('-created_at')
        
        serializer = PublicVehicleListSerializer(public_vehicles, many=True, context={'request': request})
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Public vehicles retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_public_vehicle_module_access()
@api_response
def create_public_vehicle(request):
    """Create new public vehicle with images"""
    try:
        # Extract images from request
        images_data = request.FILES.getlist('images')
        
        # Prepare data for serializer (exclude images)
        data = request.data.copy()
        if 'images' in data:
            del data['images']
        
        serializer = PublicVehicleCreateSerializer(data=data)
        
        if serializer.is_valid():
            public_vehicle = serializer.save()
            
            # Handle image uploads with titles
            image_titles = request.data.getlist('image_titles', [])
            for index, image_file in enumerate(images_data):
                title = image_titles[index] if index < len(image_titles) else None
                PublicVehicleImage.objects.create(
                    public_vehicle=public_vehicle,
                    image=image_file,
                    title=title if title else None,
                    order=index
                )
            
            # Reload to get images
            public_vehicle.refresh_from_db()
            response_serializer = PublicVehicleSerializer(public_vehicle, context={'request': request})
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Public vehicle created successfully'),
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
@require_public_vehicle_module_access(model_class=PublicVehicle, id_param_name='vehicle_id')
@api_response
def update_public_vehicle(request, vehicle_id):
    """Update public vehicle"""
    try:
        try:
            public_vehicle = PublicVehicle.objects.get(id=vehicle_id)
        except PublicVehicle.DoesNotExist:
            raise NotFoundError("Public vehicle not found")
        
        # Extract images from request
        new_images = request.FILES.getlist('images')
        images_to_delete = request.data.get('images_to_delete', [])
        
        # Get existing image titles - handle both dict and QueryDict formats
        existing_image_titles = {}
        for key in request.data.keys():
            if key.startswith('existing_image_titles[') and key.endswith(']'):
                image_id = int(key.split('[')[1].split(']')[0])
                title = request.data.get(key, '')
                existing_image_titles[image_id] = title if title else None
        
        # Prepare data for serializer (exclude images)
        data = request.data.copy()
        if 'images' in data:
            del data['images']
        if 'images_to_delete' in data:
            del data['images_to_delete']
        # Remove existing_image_titles keys
        keys_to_remove = [key for key in data.keys() if key.startswith('existing_image_titles[')]
        for key in keys_to_remove:
            del data[key]
        
        serializer = PublicVehicleCreateSerializer(public_vehicle, data=data)
        
        if serializer.is_valid():
            public_vehicle = serializer.save()
            
            # Update existing image titles
            if existing_image_titles:
                for image_id, title in existing_image_titles.items():
                    try:
                        image_obj = PublicVehicleImage.objects.get(id=image_id, public_vehicle=public_vehicle)
                        image_obj.title = title
                        image_obj.save()
                    except PublicVehicleImage.DoesNotExist:
                        pass
            
            # Delete specified images
            if images_to_delete:
                PublicVehicleImage.objects.filter(
                    id__in=images_to_delete,
                    public_vehicle=public_vehicle
                ).delete()
            
            # Add new images with titles
            existing_images_count = public_vehicle.images.count()
            image_titles = request.data.getlist('image_titles', [])
            for index, image_file in enumerate(new_images):
                title = image_titles[index] if index < len(image_titles) else None
                PublicVehicleImage.objects.create(
                    public_vehicle=public_vehicle,
                    image=image_file,
                    title=title if title else None,
                    order=existing_images_count + index
                )
            
            # Reload to get updated images
            public_vehicle.refresh_from_db()
            response_serializer = PublicVehicleSerializer(public_vehicle, context={'request': request})
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Public vehicle updated successfully')
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


@api_view(['PATCH'])
@require_public_vehicle_module_access(model_class=PublicVehicle, id_param_name='vehicle_id')
@api_response
def toggle_public_vehicle_active(request, vehicle_id):
    """Toggle is_active status of public vehicle"""
    try:
        try:
            public_vehicle = PublicVehicle.objects.get(id=vehicle_id)
        except PublicVehicle.DoesNotExist:
            raise NotFoundError("Public vehicle not found")
        
        is_active = request.data.get('is_active')
        if is_active is None:
            # Toggle if not provided
            public_vehicle.is_active = not public_vehicle.is_active
        else:
            public_vehicle.is_active = bool(is_active)
        
        public_vehicle.save()
        
        response_serializer = PublicVehicleSerializer(public_vehicle, context={'request': request})
        
        return success_response(
            data=response_serializer.data,
            message=f"Public vehicle {'activated' if public_vehicle.is_active else 'deactivated'} successfully"
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
@require_public_vehicle_module_access(model_class=PublicVehicle, id_param_name='vehicle_id')
@api_response
def delete_public_vehicle(request, vehicle_id):
    """Delete public vehicle"""
    try:
        try:
            public_vehicle = PublicVehicle.objects.get(id=vehicle_id)
        except PublicVehicle.DoesNotExist:
            raise NotFoundError("Public vehicle not found")
        
        vehicle_name = f"{public_vehicle.institute.name} - Public Vehicle #{public_vehicle.id}"
        public_vehicle.delete()
        
        return success_response(
            data={'id': vehicle_id},
            message=f"Public vehicle '{vehicle_name}' deleted successfully"
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

