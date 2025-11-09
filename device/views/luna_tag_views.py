"""
Luna Tag Views
Handles Luna Tag management endpoints
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.paginator import Paginator

from device.models import LunaTag
from device.serializers import (
    LunaTagSerializer,
    LunaTagCreateSerializer,
    LunaTagUpdateSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError, ValidationError


@api_view(['GET'])
@require_auth
@require_super_admin
@api_response
def get_all_luna_tags(request):
    """
    Get all Luna Tags (Super Admin only)
    """
    try:
        luna_tags = LunaTag.objects.all().order_by('-created_at')
        
        # Pagination
        page_number = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 25))
        paginator = Paginator(luna_tags, page_size)
        page_obj = paginator.get_page(page_number)
        
        serializer = LunaTagSerializer(page_obj, many=True)
        
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
            'luna_tags': serializer.data,
            'pagination': pagination_info
        }
        
        return success_response(
            data=response_data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Luna Tags retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@require_super_admin
@api_response
def create_luna_tag(request):
    """
    Create Luna Tag (Super Admin only)
    """
    try:
        serializer = LunaTagCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            luna_tag = serializer.save()
            response_serializer = LunaTagSerializer(luna_tag)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Luna Tag created successfully')
            )
        else:
            return error_response(
                message='Validation error',
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['PUT'])
@require_auth
@require_super_admin
@api_response
def update_luna_tag(request, id):
    """
    Update Luna Tag (Super Admin only)
    """
    try:
        try:
            luna_tag = LunaTag.objects.get(id=id)
        except LunaTag.DoesNotExist:
            return error_response(
                message='Luna Tag not found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        serializer = LunaTagUpdateSerializer(luna_tag, data=request.data, partial=True)
        
        if serializer.is_valid():
            luna_tag = serializer.save()
            response_serializer = LunaTagSerializer(luna_tag)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Luna Tag updated successfully')
            )
        else:
            return error_response(
                message='Validation error',
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['DELETE'])
@require_auth
@require_super_admin
@api_response
def delete_luna_tag(request, id):
    """
    Delete Luna Tag (Super Admin only)
    """
    try:
        try:
            luna_tag = LunaTag.objects.get(id=id)
        except LunaTag.DoesNotExist:
            return error_response(
                message='Luna Tag not found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        luna_tag.delete()
        
        return success_response(
            data=None,
            message=SUCCESS_MESSAGES.get('DATA_DELETED', 'Luna Tag deleted successfully')
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )

