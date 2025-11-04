"""
School Bus Views
Handles school bus management endpoints
"""
from rest_framework.decorators import api_view
from django.core.paginator import Paginator
from django.db.models import Q
from school.models import SchoolBus
from school.serializers import (
    SchoolBusSerializer,
    SchoolBusCreateSerializer,
    SchoolBusListSerializer
)
from fleet.models import Vehicle
from shared_utils.constants import VehicleType
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError


@api_view(['GET'])
@require_auth
@api_response
def get_school_bus_vehicles(request):
    """Get school bus vehicles with role-based access control"""
    try:
        user = request.user
        
        # Filter vehicles where vehicleType = 'SchoolBus'
        base_query = Vehicle.objects.filter(
            vehicleType=VehicleType.SCHOOL_BUS,
            is_active=True
        ).select_related('device').prefetch_related('userVehicles__user')
        
        # Get vehicles based on user role
        user_group = user.groups.first()
        if user_group and user_group.name == 'Super Admin':
            # Super Admin: Return all school bus vehicles
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
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'School bus vehicles retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_all_school_buses(request):
    """Get all school buses with pagination and filtering"""
    try:
        search_query = request.GET.get('search', '').strip()
        institute_filter = request.GET.get('institute_id', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        school_buses = SchoolBus.objects.select_related('institute', 'bus').all()
        
        if search_query:
            school_buses = school_buses.filter(
                Q(institute__name__icontains=search_query) |
                Q(bus__name__icontains=search_query) |
                Q(bus__vehicleNo__icontains=search_query)
            )
        
        if institute_filter:
            school_buses = school_buses.filter(institute_id=institute_filter)
        
        school_buses = school_buses.order_by('-created_at')
        
        paginator = Paginator(school_buses, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = SchoolBusListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'School buses retrieved successfully'),
            data={
                'school_buses': serializer.data,
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
def get_school_bus_by_id(request, bus_id):
    """Get school bus by ID"""
    try:
        try:
            school_bus = SchoolBus.objects.select_related('institute', 'bus').get(id=bus_id)
        except SchoolBus.DoesNotExist:
            raise NotFoundError("School bus not found")
        
        serializer = SchoolBusSerializer(school_bus)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'School bus retrieved successfully')
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
def get_school_buses_by_institute(request, institute_id):
    """Get school buses by institute"""
    try:
        school_buses = SchoolBus.objects.select_related('institute', 'bus').filter(
            institute_id=institute_id
        ).order_by('-created_at')
        
        serializer = SchoolBusListSerializer(school_buses, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'School buses retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_super_admin
@api_response
def create_school_bus(request):
    """Create new school bus"""
    try:
        serializer = SchoolBusCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            school_bus = serializer.save()
            response_serializer = SchoolBusSerializer(school_bus)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'School bus created successfully'),
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
def update_school_bus(request, bus_id):
    """Update school bus"""
    try:
        try:
            school_bus = SchoolBus.objects.get(id=bus_id)
        except SchoolBus.DoesNotExist:
            raise NotFoundError("School bus not found")
        
        serializer = SchoolBusCreateSerializer(school_bus, data=request.data)
        
        if serializer.is_valid():
            school_bus = serializer.save()
            response_serializer = SchoolBusSerializer(school_bus)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'School bus updated successfully')
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
def delete_school_bus(request, bus_id):
    """Delete school bus"""
    try:
        try:
            school_bus = SchoolBus.objects.get(id=bus_id)
        except SchoolBus.DoesNotExist:
            raise NotFoundError("School bus not found")
        
        bus_name = f"{school_bus.institute.name} - {school_bus.bus.name}"
        school_bus.delete()
        
        return success_response(
            data={'id': bus_id},
            message=f"School bus '{bus_name}' deleted successfully"
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

