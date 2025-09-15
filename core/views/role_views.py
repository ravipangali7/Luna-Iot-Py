"""
Role Views
Handles role and permission management endpoints
Matches Node.js role_controller.js functionality exactly
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from core.models.role import Role, RolePermission
from django.contrib.auth.models import Permission
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
    Get all roles
    Matches Node.js RoleController.getAllRoles
    """
    try:
        roles = Role.objects.all()
        roles_data = []
        
        for role in roles:
            roles_data.append({
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'createdAt': role.createdAt.isoformat(),
                'updatedAt': role.updatedAt.isoformat()
            })
        
        return success_response(
            data=roles_data,
            message=SUCCESS_MESSAGES['ROLES_RETRIEVED']
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
            message=SUCCESS_MESSAGES['PERMISSIONS_RETRIEVED']
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
    Get role by ID
    Matches Node.js RoleController.getRoleById
    """
    try:
        try:
            role = Role.objects.get(id=id)
        except Role.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['ROLE_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        role_data = {
            'id': role.id,
            'name': role.name,
            'description': role.description,
            'createdAt': role.createdAt.isoformat(),
            'updatedAt': role.updatedAt.isoformat()
        }
        
        return success_response(
            data=role_data,
            message=SUCCESS_MESSAGES['ROLE_RETRIEVED']
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
    Update role permissions
    Matches Node.js RoleController.updateRolePermissions
    """
    try:
        data = request.data
        permission_ids = data.get('permissionIds', [])
        
        try:
            role = Role.objects.get(id=id)
        except Role.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['ROLE_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Clear existing permissions
        RolePermission.objects.filter(role=role).delete()
        
        # Add new permissions
        for permission_id in permission_ids:
            try:
                permission = Permission.objects.get(id=permission_id)
                RolePermission.objects.create(role=role, permission=permission)
            except Permission.DoesNotExist:
                continue  # Skip invalid permissions
        
        # Get updated role with permissions
        role_permissions = RolePermission.objects.filter(role=role).select_related('permission')
        permissions_data = []
        
        for role_perm in role_permissions:
            permissions_data.append({
                'id': role_perm.permission.id,
                'name': role_perm.permission.name,
                'codename': role_perm.permission.codename
            })
        
        role_data = {
            'id': role.id,
            'name': role.name,
            'description': role.description,
            'permissions': permissions_data,
            'createdAt': role.createdAt.isoformat(),
            'updatedAt': role.updatedAt.isoformat()
        }
        
        return success_response(
            data=role_data,
            message=SUCCESS_MESSAGES['ROLE_UPDATED']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@api_response
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


@api_view(['PUT'])
@require_auth
@api_response
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
                message=ERROR_MESSAGES['PERMISSION_NOT_FOUND'],
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


@api_view(['DELETE'])
@require_auth
@api_response
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
                message=ERROR_MESSAGES['PERMISSION_NOT_FOUND'],
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


@api_view(['GET'])
@require_auth
@api_response
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
                message=ERROR_MESSAGES['PERMISSION_NOT_FOUND'],
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
