"""
User Views
Handles user management endpoints
Matches Node.js user_controller.js functionality exactly
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from core.models.user import User
from core.models.role import Role
from api_common.utils.response_utils import success_response, error_response
from api_common.utils.auth_utils import hash_password
from api_common.utils.validation_utils import validate_required_fields
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError, ValidationError


@api_view(['GET'])
@require_auth
@api_response
def get_all_users(request):
    """
    Get all users
    Matches Node.js UserController.getAllUsers
    """
    try:
        users = User.objects.select_related('role').all()
        users_data = []
        
        for user in users:
            users_data.append({
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'status': user.status,
                'role': user.role.name if user.role else None,
                'fcmToken': user.fcm_token,
                'createdAt': user.created_at.isoformat(),
                'updatedAt': user.updated_at.isoformat()
            })
        
        return success_response(
            data=users_data,
            message=SUCCESS_MESSAGES['USERS_RETRIEVED']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@api_response
def get_user_by_phone(request, phone):
    """
    Get user by phone
    Matches Node.js UserController.getUserByPhone
    """
    try:
        try:
            user = User.objects.select_related('role').get(phone=phone)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        user_data = {
            'id': user.id,
            'name': user.name,
            'phone': user.phone,
            'status': user.status,
            'role': user.role.name if user.role else None,
            'fcmToken': user.fcm_token,
            'createdAt': user.created_at.isoformat(),
            'updatedAt': user.updated_at.isoformat()
        }
        
        return success_response(
            data=user_data,
            message='User found'
        )
    except Exception as e:
        return error_response(
            message='Internal server error',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@api_response
def create_user(request):
    """
    Create user
    Matches Node.js UserController.createUser
    """
    try:
        data = request.data
        name = data.get('name')
        phone = data.get('phone')
        password = data.get('password')
        role_id = data.get('roleId')
        status = data.get('status')
        
        if not all([name, phone, password, role_id]):
            return error_response(
                message='Missing required fields',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Check if user already exists
        if User.objects.filter(phone=phone).exists():
            return error_response(
                message=ERROR_MESSAGES['USER_EXISTS'],
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Get role
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return error_response(
                message='Role not found',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Create user
        user = User.objects.create(
            name=name,
            phone=phone,
            password=hashed_password,
            role=role,
            status=status or 'ACTIVE'
        )
        
        user_data = {
            'id': user.id,
            'name': user.name,
            'phone': user.phone,
            'status': user.status,
            'role': user.role.name if user.role else None,
            'createdAt': user.created_at.isoformat(),
            'updatedAt': user.updated_at.isoformat()
        }
        
        return success_response(
            data=user_data,
            message=SUCCESS_MESSAGES['USER_CREATED'],
            status_code=HTTP_STATUS['CREATED']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['PUT'])
@require_auth
@api_response
def update_user(request, phone):
    """
    Update user
    Matches Node.js UserController.updateUser
    """
    try:
        data = request.data
        
        # Check if user exists
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Update user fields
        if 'name' in data:
            user.name = data['name']
        if 'phone' in data and data['phone'] != phone:
            # Check if new phone already exists
            if User.objects.filter(phone=data['phone']).exclude(id=user.id).exists():
                return error_response(
                    message='User with this phone number already exists',
                    status_code=HTTP_STATUS['BAD_REQUEST']
                )
            user.phone = data['phone']
        if 'status' in data:
            user.status = data['status']
        if 'fcmToken' in data:
            user.fcm_token = data['fcmToken']
        if 'roleId' in data:
            try:
                role = Role.objects.get(id=data['roleId'])
                user.role = role
            except Role.DoesNotExist:
                return error_response(
                    message='Role not found',
                    status_code=HTTP_STATUS['BAD_REQUEST']
                )
        
        user.save()
        
        user_data = {
            'id': user.id,
            'name': user.name,
            'phone': user.phone,
            'status': user.status,
            'role': user.role.name if user.role else None,
            'fcmToken': user.fcm_token,
            'createdAt': user.created_at.isoformat(),
            'updatedAt': user.updated_at.isoformat()
        }
        
        return success_response(
            data=user_data,
            message=SUCCESS_MESSAGES['USER_UPDATED']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['DELETE'])
@require_auth
@api_response
def delete_user(request, phone):
    """
    Delete user
    Matches Node.js UserController.deleteUser
    """
    try:
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        user.delete()
        
        return success_response(
            message=SUCCESS_MESSAGES['USER_DELETED']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['PUT'])
@require_auth
@api_response
def update_fcm_token(request):
    """
    Update FCM token
    Matches Node.js UserController.updateFcmToken
    """
    try:
        data = request.data
        phone = data.get('phone')
        fcm_token = data.get('fcmToken')
        
        if not phone or not fcm_token:
            return error_response(
                message='Phone number and FCM token are required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Check if user exists
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Update FCM token
        user.fcm_token = fcm_token
        user.save()
        
        return success_response(
            data={'fcmToken': user.fcm_token},
            message='FCM token updated successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )
