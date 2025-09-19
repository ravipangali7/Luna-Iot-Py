"""
Authentication Views
Handles authentication-related endpoints
Matches Node.js auth_controller.js functionality exactly
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import json

from core.models.user import User
from django.contrib.auth.models import Group
from core.models.otp import Otp
from api_common.utils.response_utils import success_response, error_response
from api_common.utils.auth_utils import generate_token, generate_otp
from django.contrib.auth.hashers import make_password, check_password
from api_common.utils.validation_utils import validate_required_fields, validate_phone_number
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.validation_decorators import validate_fields
from api_common.utils.sms_service import sms_service
from api_common.exceptions.auth_exceptions import InvalidCredentialsError, AccountInactiveError


@csrf_exempt
@require_http_methods(["GET"])
def get_current_user(request):
    """
    Get current user information
    Matches Node.js AuthController.getCurrentUser
    """
    try:
        user = request.user
        
        # Check if user exists
        if not user or not hasattr(user, 'id'):
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Get all user roles with their permissions
        user_groups = user.groups.all()
        roles_data = []
        all_permissions = set()
        
        for group in user_groups:
            # Get role permissions
            group_permissions = list(group.permissions.values_list('name', flat=True))
            all_permissions.update(group_permissions)
            
            roles_data.append({
                'id': group.id,
                'name': group.name,
                'permissions': group_permissions
            })
        
        # Get direct user permissions
        direct_permissions = list(user.user_permissions.values_list('name', flat=True))
        all_permissions.update(direct_permissions)
        
        # Get all available permissions for UI
        from django.contrib.auth.models import Permission
        all_available_permissions = list(Permission.objects.values('id', 'name', 'content_type__app_label', 'content_type__model'))
        
        return success_response(
            data={
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'status': 'ACTIVE' if user.is_active else 'INACTIVE',
                'roles': roles_data,  # All user roles with their permissions
                'permissions': list(all_permissions),  # All permissions (role + direct)
                'directPermissions': direct_permissions,  # Only direct user permissions
                'availablePermissions': all_available_permissions,  # All available permissions for UI
                'createdAt': user.created_at.isoformat(),
                'updatedAt': user.updated_at.isoformat()
            },
            message=SUCCESS_MESSAGES['USER_RETRIEVED']
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(
            message=f"Internal server error: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@csrf_exempt
@require_http_methods(["POST"])
@api_response
def send_registration_otp(request):
    """
    Send OTP for registration
    Matches Node.js AuthController.sendRegistrationOTP
    """
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        phone = data.get('phone')
        
        if not phone:
            return error_response(
                message='Phone number is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Check if user already exists
        if User.objects.filter(phone=phone).exists():
            return error_response(
                message=ERROR_MESSAGES['USER_EXISTS'],
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Generate OTP
        otp = generate_otp()
        
        # Save OTP to database
        Otp.objects.filter(phone=phone).delete()  # Delete existing OTPs
        Otp.objects.create(phone=phone, otp=otp)
        
        # TODO: Send SMS (implement SMS service)
        # sms_result = sms_service.sendOTP(phone, otp)
        
        return success_response(
            data={
                'phone': phone,
                'message': 'OTP sent to your phone number'
            },
            message=SUCCESS_MESSAGES['OTP_SENT']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@csrf_exempt
@require_http_methods(["POST"])
@api_response
def verify_otp_and_register(request):
    """
    Verify OTP and register user
    Matches Node.js AuthController.verifyOTPAndRegister
    """
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        name = data.get('name')
        phone = data.get('phone')
        password = data.get('password')
        otp = data.get('otp')
        
        if not all([name, phone, password, otp]):
            return error_response(
                message='All fields are required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Check if user already exists
        if User.objects.filter(phone=phone.strip()).exists():
            return error_response(
                message=ERROR_MESSAGES['USER_EXISTS'],
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Verify OTP
        try:
            otp_record = Otp.objects.get(phone=phone.strip(), otp=otp)
            if otp_record.is_expired():
                return error_response(
                    message='Invalid or expired OTP',
                    status_code=HTTP_STATUS['BAD_REQUEST']
                )
        except Otp.DoesNotExist:
            return error_response(
                message='Invalid or expired OTP',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Hash password using Django's built-in hasher
        hashed_password = make_password(password)
        
        # Generate token
        token = generate_token()
        
        # Get default group
        try:
            default_group = Group.objects.get(name='Customer')
        except Group.DoesNotExist:
            return error_response(
                message='Default group not found',
                status_code=HTTP_STATUS['INTERNAL_ERROR']
            )
        
        # Create user
        user = User.objects.create(
            name=name.strip(),
            phone=phone.strip(),
            password=hashed_password,
            token=token,
            is_active=True
        )
        
        # Assign default group to user
        # Using Django's built-in Group system
        try:
            default_group = Group.objects.get(name='Customer')
            user.groups.add(default_group)
        except Group.DoesNotExist:
            # If Customer group doesn't exist, create it
            default_group = Group.objects.create(name='Customer')
            user.groups.add(default_group)
        
        # Delete OTP after successful registration
        otp_record.delete()
        
        # Get role data for new user
        roles_data = [{
            'id': default_group.id,
            'name': default_group.name,
            'permissions': list(default_group.permissions.values_list('name', flat=True))
        }]
        
        return success_response(
            data={
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'token': user.token,
                'role': default_group.name,  # Primary role for backward compatibility
                'roles': roles_data,  # All user roles with their permissions
                'permissions': list(default_group.permissions.values_list('name', flat=True)),  # All permissions
                'directPermissions': [],  # No direct permissions for new user
            },
            message=SUCCESS_MESSAGES['REGISTRATION_SUCCESS'],
            status_code=HTTP_STATUS['CREATED']
        )
    except Exception as e:
        return error_response(
            message=f'Registration failed: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@csrf_exempt
@require_http_methods(["POST"])
@api_response
def resend_otp(request):
    """
    Resend OTP
    Matches Node.js AuthController.resendOTP
    """
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        phone = data.get('phone')
        
        if not phone:
            return error_response(
                message='Phone number is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Check if user already exists
        if User.objects.filter(phone=phone).exists():
            return error_response(
                message=ERROR_MESSAGES['USER_EXISTS'],
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Generate new OTP
        otp = generate_otp()
        
        # Save new OTP to database
        Otp.objects.filter(phone=phone).delete()  # Delete existing OTPs
        Otp.objects.create(phone=phone, otp=otp)
        
        # TODO: Send SMS (implement SMS service)
        # sms_result = sms_service.sendOTP(phone, otp)
        
        return success_response(
            data={
                'phone': phone,
                'message': 'New OTP sent to your phone number'
            },
            message='OTP resent successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    """
    User login
    Matches Node.js AuthController.login
    """
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        phone = data.get('phone')
        password = data.get('password')
        
        # Find user by phone
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Check password using Django's built-in checker
        if not check_password(password, user.password):
            return error_response(
                message=ERROR_MESSAGES['INVALID_CREDENTIALS'],
                status_code=HTTP_STATUS['UNAUTHORIZED']
            )
        
        # Check if user is active
        if not user.is_active:
            return error_response(
                message='User account is not active',
                status_code=HTTP_STATUS['UNAUTHORIZED']
            )
        
        # Generate new token for login
        token = generate_token()
        user.token = token
        user.save()
        
        # Get all user roles with their permissions
        user_groups = user.groups.all()
        roles_data = []
        all_permissions = set()
        
        for group in user_groups:
            # Get role permissions
            group_permissions = list(group.permissions.values_list('name', flat=True))
            all_permissions.update(group_permissions)
            
            roles_data.append({
                'id': group.id,
                'name': group.name,
                'permissions': group_permissions
            })
        
        # Get direct user permissions
        direct_permissions = list(user.user_permissions.values_list('name', flat=True))
        all_permissions.update(direct_permissions)
        
        # Get primary role for backward compatibility
        primary_role = user_groups.first()
        primary_role_name = primary_role.name if primary_role else None
        
        return success_response(
            data={
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'token': user.token,
                'role': primary_role_name,  # Primary role for backward compatibility
                'roles': roles_data,  # All user roles with their permissions
                'permissions': list(all_permissions),  # All permissions (role + direct)
                'directPermissions': direct_permissions,  # Only direct user permissions
            },
            message=SUCCESS_MESSAGES['LOGIN_SUCCESS']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@api_response
def logout(request):
    """
    User logout
    Matches Node.js AuthController.logout
    """
    try:
        user = request.user
        user.token = None
        user.save()
        
        return success_response(
            message=SUCCESS_MESSAGES['LOGOUT_SUCCESS']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@csrf_exempt
@require_http_methods(["POST"])
@api_response
def send_forgot_password_otp(request):
    """
    Send OTP for forgot password
    Matches Node.js AuthController.sendForgotPasswordOTP
    """
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        phone = data.get('phone')
        
        if not phone:
            return error_response(
                message='Phone number is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Check if user exists
        if not User.objects.filter(phone=phone).exists():
            return error_response(
                message='User not found with this phone number',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Generate OTP
        otp = generate_otp()
        
        # Save OTP to database
        Otp.objects.filter(phone=phone).delete()  # Delete existing OTPs
        Otp.objects.create(phone=phone, otp=otp)
        
        # TODO: Send SMS (implement SMS service)
        # sms_result = sms_service.sendOTP(phone, otp)
        
        return success_response(
            data={
                'phone': phone,
                'message': 'OTP sent to your phone number'
            },
            message=SUCCESS_MESSAGES['OTP_SENT']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@csrf_exempt
@require_http_methods(["POST"])
@api_response
def verify_forgot_password_otp(request):
    """
    Verify OTP for forgot password
    Matches Node.js AuthController.verifyForgotPasswordOTP
    """
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        phone = data.get('phone')
        otp = data.get('otp')
        
        if not phone or not otp:
            return error_response(
                message='Phone number and OTP are required',
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
        
        # Verify OTP
        try:
            otp_record = Otp.objects.get(phone=phone, otp=otp)
            if otp_record.is_expired():
                return error_response(
                    message='Invalid or expired OTP',
                    status_code=HTTP_STATUS['BAD_REQUEST']
                )
        except Otp.DoesNotExist:
            return error_response(
                message='Invalid or expired OTP',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Generate reset token (valid for 10 minutes)
        reset_token = generate_token()
        
        # Store reset token in user record
        user.token = reset_token
        user.save()
        
        return success_response(
            data={
                'phone': phone,
                'resetToken': reset_token
            },
            message='OTP verified successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@csrf_exempt
@require_http_methods(["POST"])
@api_response
def reset_password(request):
    """
    Reset password
    Matches Node.js AuthController.resetPassword
    """
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        phone = data.get('phone')
        reset_token = data.get('resetToken')
        new_password = data.get('newPassword')
        
        if not all([phone, reset_token, new_password]):
            return error_response(
                message='Phone number, reset token, and new password are required',
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
        
        # Verify reset token
        if user.token != reset_token:
            return error_response(
                message='Invalid reset token',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Hash new password using Django's built-in hasher
        hashed_password = make_password(new_password)
        
        # Generate new token
        new_token = generate_token()
        
        # Update user with new password and token
        user.password = hashed_password
        user.token = new_token
        user.save()
        
        # Delete OTP after successful password reset
        Otp.objects.filter(phone=phone).delete()
        
        # Get all user roles with their permissions
        user_groups = user.groups.all()
        roles_data = []
        all_permissions = set()
        
        for group in user_groups:
            # Get role permissions
            group_permissions = list(group.permissions.values_list('name', flat=True))
            all_permissions.update(group_permissions)
            
            roles_data.append({
                'id': group.id,
                'name': group.name,
                'permissions': group_permissions
            })
        
        # Get direct user permissions
        direct_permissions = list(user.user_permissions.values_list('name', flat=True))
        all_permissions.update(direct_permissions)
        
        return success_response(
            data={
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'token': user.token,
                'roles': roles_data,  # All user roles with their permissions
                'permissions': list(all_permissions),  # All permissions (role + direct)
                'directPermissions': direct_permissions,  # Only direct user permissions
            },
            message=SUCCESS_MESSAGES['PASSWORD_RESET']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )