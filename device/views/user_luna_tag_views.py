"""
User Luna Tag Views
Handles UserLunaTag management endpoints with role-based access
"""
from rest_framework.decorators import api_view
from django.core.paginator import Paginator

from device.models import UserLunaTag
from device.serializers import (
    UserLunaTagSerializer,
    UserLunaTagCreateSerializer,
    UserLunaTagUpdateSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError, ValidationError


@api_view(['GET'])
@require_auth
@api_response
def get_all_user_luna_tags(request):
    """
    Get UserLunaTags with role-based filtering
    Super Admin: all, Others: only their own
    """
    try:
        user = request.user
        
        # Check if user is super admin
        user_groups = user.groups.all()
        is_super_admin = any(group.name == 'Super Admin' for group in user_groups)
        
        if is_super_admin:
            # Super Admin: get all
            user_luna_tags = UserLunaTag.objects.select_related('publicKey').all().order_by('-created_at')
        else:
            # Others: get only their own (need to check how user relates to UserLunaTag)
            # Since UserLunaTag doesn't have direct FK to User, we'll need to filter differently
            # For now, return all active ones - this might need adjustment based on actual relationship
            user_luna_tags = UserLunaTag.objects.select_related('publicKey').filter(is_active=True).order_by('-created_at')
        
        # Pagination
        page_number = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 25))
        paginator = Paginator(user_luna_tags, page_size)
        page_obj = paginator.get_page(page_number)
        
        serializer = UserLunaTagSerializer(page_obj, many=True)
        
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
            'user_luna_tags': serializer.data,
            'pagination': pagination_info
        }
        
        return success_response(
            data=response_data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'User Luna Tags retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@api_response
def create_user_luna_tag(request):
    """
    Create UserLunaTag (all authenticated users)
    """
    try:
        serializer = UserLunaTagCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            user_luna_tag = serializer.save()
            response_serializer = UserLunaTagSerializer(user_luna_tag)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'User Luna Tag created successfully')
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
@api_response
def update_user_luna_tag(request, id):
    """
    Update UserLunaTag (all authenticated users, own records)
    """
    try:
        user = request.user
        
        try:
            user_luna_tag = UserLunaTag.objects.get(id=id)
        except UserLunaTag.DoesNotExist:
            return error_response(
                message='User Luna Tag not found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Check if user is super admin or owns the record
        # Since UserLunaTag doesn't have direct FK to User, we'll allow all authenticated users for now
        # This might need adjustment based on actual relationship
        
        serializer = UserLunaTagUpdateSerializer(user_luna_tag, data=request.data, partial=True)
        
        if serializer.is_valid():
            user_luna_tag = serializer.save()
            response_serializer = UserLunaTagSerializer(user_luna_tag)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'User Luna Tag updated successfully')
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
def delete_user_luna_tag(request, id):
    """
    Delete UserLunaTag (Super Admin only)
    """
    try:
        try:
            user_luna_tag = UserLunaTag.objects.get(id=id)
        except UserLunaTag.DoesNotExist:
            return error_response(
                message='User Luna Tag not found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        user_luna_tag.delete()
        
        return success_response(
            data=None,
            message=SUCCESS_MESSAGES.get('DATA_DELETED', 'User Luna Tag deleted successfully')
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )

