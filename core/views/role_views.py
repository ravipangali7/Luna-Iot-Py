"""
Group Views (formerly Role Views)
Handles group and permission management endpoints using Django's built-in Group system
Matches Node.js role_controller.js functionality exactly
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth.models import Group, Permission
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth
from api_common.exceptions.api_exceptions import NotFoundError, ValidationError


@api_view(['GET'])
@require_auth
@api_response
def get_all_roles(request):
    """
    Get all groups (roles)
    Matches Node.js RoleController.getAllRoles
    """
    try:
        groups = Group.objects.all()
        groups_data = []
        
        for group in groups:
            groups_data.append({
                'id': group.id,
                'name': group.name,
                'permissions': list(group.permissions.values_list('name', flat=True)),
                'permission_count': group.permissions.count()
            })
        
        return success_response(
            data=groups_data,
            message=SUCCESS_MESSAGES.get('ROLES_RETRIEVED', 'Groups retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET', 'POST'])
@require_auth
@api_response
def permission_handler(request):
    """
    Handle permission operations based on HTTP method
    Routes GET, POST requests to appropriate handlers
    """
    if request.method == 'GET':
        return get_all_permissions(request)
    elif request.method == 'POST':
        return create_permission(request)
    else:
        return error_response(
            message='Method not allowed',
            status_code=405
        )


@api_view(['GET', 'PUT', 'DELETE'])
@require_auth
@api_response
def permission_by_id_handler(request, id):
    """
    Handle permission operations by ID based on HTTP method
    Routes GET, PUT, DELETE requests to appropriate handlers
    """
    if request.method == 'GET':
        return get_permission_by_id(request, id)
    elif request.method == 'PUT':
        return update_permission(request, id)
    elif request.method == 'DELETE':
        return delete_permission(request, id)
    else:
        return error_response(
            message='Method not allowed',
            status_code=405
        )


def get_all_permissions(request):
    """
    Get all permissions
    Matches Node.js RoleController.getAllPermissions
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
            message=SUCCESS_MESSAGES.get('PERMISSIONS_RETRIEVED', 'Permissions retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_role_by_id(request, id):
    """
    Get group by ID
    Matches Node.js RoleController.getRoleById
    """
    try:
        try:
            group = Group.objects.get(id=id)
        except Group.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES.get('ROLE_NOT_FOUND', 'Group not found'),
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        group_data = {
            'id': group.id,
            'name': group.name,
            'permissions': list(group.permissions.values_list('name', flat=True)),
            'permission_count': group.permissions.count()
        }
        
        return success_response(
            data=group_data,
            message=SUCCESS_MESSAGES.get('ROLE_RETRIEVED', 'Group retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['PUT'])
@require_auth
@api_response
def update_role_permissions(request, id):
    """
    Update group permissions
    Matches Node.js RoleController.updateRolePermissions
    """
    try:
        data = request.data
        permission_ids = data.get('permissionIds', [])
        
        try:
            group = Group.objects.get(id=id)
        except Group.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES.get('ROLE_NOT_FOUND', 'Group not found'),
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Clear existing permissions
        group.permissions.clear()
        
        # Add new permissions
        for permission_id in permission_ids:
            try:
                permission = Permission.objects.get(id=permission_id)
                group.permissions.add(permission)
            except Permission.DoesNotExist:
                continue  # Skip invalid permissions
        
        # Get updated group with permissions
        permissions_data = []
        for permission in group.permissions.all():
            permissions_data.append({
                'id': permission.id,
                'name': permission.name,
                'codename': permission.codename
            })
        
        group_data = {
            'id': group.id,
            'name': group.name,
            'permissions': permissions_data,
            'permission_count': group.permissions.count()
        }
        
        return success_response(
            data=group_data,
            message=SUCCESS_MESSAGES.get('ROLE_UPDATED', 'Group updated successfully')
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


def create_permission(request):
    """
    Create permission
    Matches Node.js RoleController.createPermission
    """
    try:
        data = request.data
        name = data.get('name')
        description = data.get('description')
        
        if not name or name.strip() == '':
            return error_response(
                message='Permission name is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Create permission
        permission = Permission.objects.create(
            name=name.strip(),
            codename=name.strip().lower().replace(' ', '_'),
            content_type_id=1  # Default content type
        )
        
        permission_data = {
            'id': permission.id,
            'name': permission.name,
            'codename': permission.codename,
            'description': description.strip() if description else None
        }
        
        return success_response(
            data=permission_data,
            message='Permission created successfully',
            status_code=HTTP_STATUS['CREATED']
        )
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e) or 'duplicate key' in str(e).lower():
            return error_response(
                message='Permission with this name already exists',
                status_code=HTTP_STATUS['CONFLICT']
            )
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


def update_permission(request, id):
    """
    Update permission
    Matches Node.js RoleController.updatePermission
    """
    try:
        data = request.data
        name = data.get('name')
        description = data.get('description')
        
        if not name or name.strip() == '':
            return error_response(
                message='Permission name is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        try:
            permission = Permission.objects.get(id=id)
        except Permission.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES.get('PERMISSION_NOT_FOUND', 'Permission not found'),
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Update permission
        permission.name = name.strip()
        permission.codename = name.strip().lower().replace(' ', '_')
        permission.save()
        
        permission_data = {
            'id': permission.id,
            'name': permission.name,
            'codename': permission.codename,
            'description': description.strip() if description else None
        }
        
        return success_response(
            data=permission_data,
            message='Permission updated successfully'
        )
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e) or 'duplicate key' in str(e).lower():
            return error_response(
                message='Permission with this name already exists',
                status_code=HTTP_STATUS['CONFLICT']
            )
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


def delete_permission(request, id):
    """
    Delete permission
    Matches Node.js RoleController.deletePermission
    """
    try:
        try:
            permission = Permission.objects.get(id=id)
        except Permission.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES.get('PERMISSION_NOT_FOUND', 'Permission not found'),
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        permission.delete()
        
        return success_response(
            message='Permission deleted successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


def get_permission_by_id(request, id):
    """
    Get permission by ID
    Matches Node.js RoleController.getPermissionById
    """
    try:
        try:
            permission = Permission.objects.get(id=id)
        except Permission.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES.get('PERMISSION_NOT_FOUND', 'Permission not found'),
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        permission_data = {
            'id': permission.id,
            'name': permission.name,
            'codename': permission.codename,
            'content_type': permission.content_type.app_label
        }
        
        return success_response(
            data=permission_data,
            message='Permission retrieved successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )