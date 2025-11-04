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

