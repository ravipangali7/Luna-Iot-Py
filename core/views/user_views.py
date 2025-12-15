"""
User Views
Handles user management endpoints
Matches Node.js user_controller.js functionality exactly
"""
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from core.models.user import User
from django.contrib.auth.models import Group
from api_common.utils.response_utils import success_response, error_response
from django.contrib.auth.hashers import make_password
from api_common.utils.validation_utils import validate_required_fields
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError, ValidationError
from decimal import Decimal


@api_view(['GET'])
@require_auth
@api_response
def get_light_users(request):
    """
    Get all users (lightweight version for dropdowns/selects)
    Optimized for performance - only returns essential fields
    """
    try:
        # Use values() for direct database serialization (10-50x faster)
        users = User.objects.values('id', 'name', 'phone', 'is_active').all()
        
        # Use list comprehension for efficient serialization
        users_data = [
            {
                'id': user['id'],
                'name': user['name'] or '',
                'phone': user['phone'],
                'status': 'ACTIVE' if user['is_active'] else 'INACTIVE'
            }
            for user in users
        ]
        
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
@require_auth
@api_response
def get_all_users(request):
    """
    Get all users
    Matches Node.js UserController.getAllUsers
    """
    try:
        users = User.objects.prefetch_related('groups').all()
        users_data = []
        
        for user in users:
            user_group = user.groups.first()
            users_data.append({
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'status': 'ACTIVE' if user.is_active else 'INACTIVE',
                'role': user_group.name if user_group else None,
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
@require_auth
@api_response
def get_users_paginated(request):
    """
    Get users with pagination and search
    """
    try:
        # Get filter parameters
        search_query = request.GET.get('search', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # Start with all users
        users = User.objects.prefetch_related('groups').all()
        
        # Apply search filter
        if search_query:
            users = users.filter(
                Q(name__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        # Order by created_at descending
        users = users.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(users, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        users_data = []
        for user in page_obj.object_list:
            user_group = user.groups.first()
            users_data.append({
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'email': user.email,
                'status': 'ACTIVE' if user.is_active else 'INACTIVE',
                'role': user_group.name if user_group else None,
                'fcmToken': user.fcm_token,
                'createdAt': user.created_at.isoformat(),
                'updatedAt': user.updated_at.isoformat()
            })
        
        return success_response(
            message=SUCCESS_MESSAGES['DATA_RETRIEVED'],
            data={
                'users': users_data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'page_size': page_size,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                },
                'search_query': search_query
            }
        )
        
    except Exception as e:
        return error_response(
            message="Error retrieving users",
            data=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET', 'PUT', 'DELETE'])
@api_response
def user_by_phone_handler(request, phone):
    """
    Handle user operations by phone based on HTTP method
    Routes GET, PUT, DELETE requests to appropriate handlers
    """
    if request.method == 'GET':
        return get_user_by_phone(request, phone)
    elif request.method == 'PUT':
        return update_user(request, phone)
    elif request.method == 'DELETE':
        return delete_user(request, phone)
    else:
        return error_response(
            message='Method not allowed',
            status_code=405
        )


def get_user_by_phone(request, phone):
    """
    Get user by phone
    Matches Node.js UserController.getUserByPhone
    """
    try:
        try:
            user = User.objects.prefetch_related('groups').get(phone=phone)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        user_group = user.groups.first()
        user_data = {
            'id': user.id,
            'name': user.name,
            'phone': user.phone,
            'status': 'ACTIVE' if user.is_active else 'INACTIVE',
            'role': user_group.name if user_group else None,
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
        hashed_password = make_password(password)
        
        # Get group
        try:
            group = Group.objects.get(id=role_id)
        except Group.DoesNotExist:
            return error_response(
                message='Group not found',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Create user
        user = User.objects.create(
            name=name,
            phone=phone,
            password=hashed_password,
            is_active=(status == 'ACTIVE') if status else True
        )
        
        # Assign group to user
        user.groups.add(group)
        
        # Create wallet for the new user
        from finance.models import Wallet
        Wallet.objects.create(
            user=user,
            balance=Decimal('7.5')
        )
        
        # Get user's primary group
        user_group = user.groups.first()
        
        user_data = {
            'id': user.id,
            'name': user.name,
            'phone': user.phone,
            'status': 'ACTIVE' if user.is_active else 'INACTIVE',
            'role': user_group.name if user_group else None,
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
                group = Group.objects.get(id=data['roleId'])
                user.groups.clear()
                user.groups.add(group)
            except Group.DoesNotExist:
                return error_response(
                    message='Group not found',
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
