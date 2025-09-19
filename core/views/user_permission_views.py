"""
User Permission Views
Handles user permission management endpoints
Matches Node.js user_permission_controller.js functionality exactly
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from core.models.user import User
from django.contrib.auth.models import Permission
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth
from api_common.exceptions.api_exceptions import NotFoundError, ValidationError


@api_view(['GET'])
@require_auth
@api_response
def get_user_permissions(request, userId):
    """
    Get all permissions for a user
    Matches Node.js UserPermissionController.getUserPermissions
    """
    try:
        try:
            user = User.objects.get(id=userId)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Get user permissions
        user_permissions = user.userpermission_set.select_related('permission').all()
        permissions_data = []
        
        for user_perm in user_permissions:
            permissions_data.append({
                'id': user_perm.id,
                'userId': userId,
                'permissionId': user_perm.permission.id,
                'permission': {
                    'id': user_perm.permission.id,
                    'name': user_perm.permission.name,
                    'codename': user_perm.permission.codename,
                },
                'createdAt': user_perm.created_at.isoformat() if hasattr(user_perm, 'created_at') else None
            })
        
        return success_response(
            data=permissions_data,
            message='User permissions retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_combined_user_permissions(request, userId):
    """
    Get combined permissions (role + direct) for a user
    Matches Node.js UserPermissionController.getCombinedUserPermissions
    """
    try:
        try:
            user = User.objects.prefetch_related('roles', 'userpermission_set__permission').get(id=userId)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Get group permissions
        group_permissions = []
        for group in user.groups.all():
            group_permissions.extend(group.permissions.values_list('name', flat=True))
        
        # Get direct user permissions
        direct_permissions = list(user.userpermission_set.values_list('permission__name', flat=True))
        
        # Combine and deduplicate
        all_permissions = list(set(group_permissions + direct_permissions))
        
        return success_response(
            data={'permissions': all_permissions},
            message='Combined user permissions retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@api_response
def assign_permission_to_user(request):
    """
    Assign permission to user
    Matches Node.js UserPermissionController.assignPermissionToUser
    """
    try:
        data = request.data
        user_id = data.get('userId')
        permission_id = data.get('permissionId')
        
        if not user_id or not permission_id:
            return error_response(
                message='User ID and Permission ID are required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        try:
            permission = Permission.objects.get(id=permission_id)
        except Permission.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['PERMISSION_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Check if permission already assigned
        if user.userpermission_set.filter(permission=permission).exists():
            return error_response(
                message='Permission already assigned to user',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Assign permission
        user.userpermission_set.create(permission=permission)
        
        return success_response(
            data={
                'userId': user_id,
                'permissionId': permission_id,
                'permissionName': permission.name
            },
            message='Permission assigned to user successfully',
            status_code=HTTP_STATUS['CREATED']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['DELETE'])
@require_auth
@api_response
def remove_permission_from_user(request):
    """
    Remove permission from user
    Matches Node.js UserPermissionController.removePermissionFromUser
    """
    try:
        data = request.data
        user_id = data.get('userId')
        permission_id = data.get('permissionId')
        
        if not user_id or not permission_id:
            return error_response(
                message='User ID and Permission ID are required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        try:
            permission = Permission.objects.get(id=permission_id)
        except Permission.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['PERMISSION_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Remove permission
        deleted_count, _ = user.userpermission_set.filter(permission=permission).delete()
        
        if deleted_count > 0:
            return success_response(
                message='Permission removed from user successfully'
            )
        else:
            return error_response(
                message='Permission not found for user',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@api_response
def assign_multiple_permissions_to_user(request):
    """
    Assign multiple permissions to user
    Matches Node.js UserPermissionController.assignMultiplePermissionsToUser
    """
    try:
        data = request.data
        user_id = data.get('userId')
        permission_ids = data.get('permissionIds', [])
        
        if not user_id or not permission_ids or not isinstance(permission_ids, list):
            return error_response(
                message='User ID and Permission IDs array are required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Get valid permissions
        valid_permissions = Permission.objects.filter(id__in=permission_ids)
        
        # Assign permissions
        assigned_permissions = []
        for permission in valid_permissions:
            if not user.userpermission_set.filter(permission=permission).exists():
                user.userpermission_set.create(permission=permission)
                assigned_permissions.append({
                    'id': permission.id,
                    'name': permission.name
                })
        
        return success_response(
            data={
                'userId': user_id,
                'assignedPermissions': assigned_permissions
            },
            message='Permissions assigned to user successfully',
            status_code=HTTP_STATUS['CREATED']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['DELETE'])
@require_auth
@api_response
def remove_all_permissions_from_user(request, userId):
    """
    Remove all permissions from user
    Matches Node.js UserPermissionController.removeAllPermissionsFromUser
    """
    try:
        if not userId:
            return error_response(
                message='User ID is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        try:
            user = User.objects.get(id=userId)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Remove all permissions
        removed_count, _ = user.userpermission_set.all().delete()
        
        return success_response(
            data={'removedCount': removed_count},
            message='All permissions removed from user successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def check_user_permission(request, userId, permissionName):
    """
    Check if user has specific permission
    Matches Node.js UserPermissionController.checkUserPermission
    """
    try:
        if not userId or not permissionName:
            return error_response(
                message='User ID and Permission Name are required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        try:
            user = User.objects.prefetch_related('roles', 'userpermission_set__permission').get(id=userId)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Check group permissions
        has_group_permission = False
        for group in user.groups.all():
            if group.permissions.filter(name=permissionName).exists():
                has_group_permission = True
                break
        
        # Check direct permissions
        has_direct_permission = user.userpermission_set.filter(permission__name=permissionName).exists()
        
        has_permission = has_group_permission or has_direct_permission
        
        return success_response(
            data={'hasPermission': has_permission},
            message='Permission check completed successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_all_permissions(request):
    """
    Get all available permissions
    Matches Node.js UserPermissionController.getAllPermissions
    """
    try:
        permissions = Permission.objects.all()
        permissions_data = []
        
        for permission in permissions:
            permissions_data.append({
                'id': permission.id,
                'name': permission.name,
                'codename': permission.codename,
                'content_type': permission.content_type.app_label
            })
        
        return success_response(
            data=permissions_data,
            message='All permissions retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_users_with_permission(request, permissionId):
    """
    Get users with specific permission
    Matches Node.js UserPermissionController.getUsersWithPermission
    """
    try:
        if not permissionId:
            return error_response(
                message='Permission ID is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        try:
            permission = Permission.objects.get(id=permissionId)
        except Permission.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['PERMISSION_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Get users with this permission
        users = User.objects.filter(userpermission_set__permission=permission).prefetch_related('groups')
        users_data = []
        
        for user in users:
            user_roles = [{'id': group.id, 'name': group.name} for group in user.groups.all()]
            users_data.append({
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'roles': user_roles,
                'is_active': user.is_active
            })
        
        return success_response(
            data=users_data,
            message='Users with permission retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )
