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
from django.core.files.storage import default_storage
from api_common.constants.validation_constants import FILE_UPLOAD_LIMITS


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
        
        # Check if user is active
        if not user.is_active:
            return error_response(
                message='Your account is deleted. Please contact administration.',
                status_code=HTTP_STATUS['UNAUTHORIZED']
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
        
        # Get direct user permissions from Django's built-in system
        django_direct_permissions = list(user.user_permissions.values_list('name', flat=True))
        all_permissions.update(django_direct_permissions)
        
        # Get direct user permissions from custom UserPermission model
        custom_direct_permissions = list(user.userpermission_set.values_list('permission__name', flat=True))
        all_permissions.update(custom_direct_permissions)
        
        # Combine all direct permissions for backward compatibility
        direct_permissions = list(set(django_direct_permissions + custom_direct_permissions))
        
        # Get all available permissions for UI
        from django.contrib.auth.models import Permission
        all_available_permissions = list(Permission.objects.values('id', 'name', 'content_type__app_label', 'content_type__model'))
        
        # Get profile picture URL
        profile_picture_url = None
        if user.profile_picture:
            from django.conf import settings
            profile_picture_url = f"{settings.MEDIA_URL}{user.profile_picture.name}"
        
        return success_response(
            data={
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'profilePicture': profile_picture_url,
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
        
        # Send SMS
        sms_result = sms_service.send_otp(phone, otp)
        print(f"SMS send result for {phone}: {sms_result}")
        
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
        
        # Create wallet for the new user
        from finance.models import Wallet
        Wallet.objects.create(
            user=user,
            balance=0.00
        )
        
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
        
        # Send SMS
        sms_result = sms_service.send_otp(phone, otp)
        print(f"SMS send result for {phone}: {sms_result}")
        
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
                message='Your account is deleted. Please contact administration.',
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
        
        # Get direct user permissions from Django's built-in system
        django_direct_permissions = list(user.user_permissions.values_list('name', flat=True))
        all_permissions.update(django_direct_permissions)
        
        # Get direct user permissions from custom UserPermission model
        custom_direct_permissions = list(user.userpermission_set.values_list('permission__name', flat=True))
        all_permissions.update(custom_direct_permissions)
        
        # Combine all direct permissions for backward compatibility
        direct_permissions = list(set(django_direct_permissions + custom_direct_permissions))
        
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
        
        # Send SMS
        sms_result = sms_service.send_otp(phone, otp)
        print(f"SMS send result for {phone}: {sms_result}")
        
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


@api_view(['POST'])
@api_response
def verify_password(request):
    """
    Verify user password before sensitive operations
    """
    try:
        user = request.user
        
        # Check if user exists
        if not user or not hasattr(user, 'id'):
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        import json
        data = json.loads(request.body) if request.body else {}
        password = data.get('password')
        
        if not password:
            return error_response(
                message='Password is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Verify password using Django's built-in checker
        if not check_password(password, user.password):
            return error_response(
                message='Incorrect password',
                status_code=HTTP_STATUS['UNAUTHORIZED']
            )
        
        return success_response(
            message='Password verified successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@api_response
def delete_account(request):
    """
    Delete user account (deactivate account)
    Sets user.is_active = False instead of permanent deletion
    """
    try:
        user = request.user
        
        # Check if user exists
        if not user or not hasattr(user, 'id'):
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Deactivate user account instead of deleting
        user.is_active = False
        user.token = None  # Invalidate token
        user.biometric_token = None  # Invalidate biometric token
        user.save()
        
        return success_response(
            message='Account has been deleted successfully. Please contact administration to reactivate your account.'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@csrf_exempt
@require_http_methods(["GET", "POST"])
@api_response
def delete_account_public(request):
    """
    Public endpoint to delete user account by phone and password
    No authentication required - verifies credentials via phone and password
    Deactivates the user account (sets is_active = False) instead of permanent deletion
    """
    try:
        # Get phone and password from query parameters
        phone = request.GET.get('phone')
        password = request.GET.get('password')
        
        # Check if phone and password are provided
        if not phone:
            return error_response(
                message='Phone number is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        if not password:
            return error_response(
                message='Password is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Find user by phone
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Verify password using Django's built-in checker
        if not check_password(password, user.password):
            return error_response(
                message='Invalid phone number or password',
                status_code=HTTP_STATUS['UNAUTHORIZED']
            )
        
        # Deactivate user account instead of deleting
        user.is_active = False
        user.token = None  # Invalidate token
        user.biometric_token = None  # Invalidate biometric token
        user.save()
        
        return success_response(
            message='Account has been deleted successfully. Please contact administration to reactivate your account.'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@csrf_exempt
@require_http_methods(["POST"])
@api_response
def biometric_login(request):
    """
    Biometric login using stored biometric token
    Matches Node.js AuthController.biometricLogin
    """
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        phone = data.get('phone')
        biometric_token = data.get('biometric_token')
        
        if not phone or not biometric_token:
            return error_response(
                message='Phone number and biometric token are required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Find user by phone
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Check if user is active
        if not user.is_active:
            return error_response(
                message='Your account is deleted. Please contact administration.',
                status_code=HTTP_STATUS['UNAUTHORIZED']
            )
        
        # Verify biometric token
        if not user.biometric_token or user.biometric_token != biometric_token:
            return error_response(
                message='Invalid biometric credentials',
                status_code=HTTP_STATUS['UNAUTHORIZED']
            )
        
        # Generate new session token for this login
        new_token = generate_token()
        user.token = new_token
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
        
        # Get direct user permissions from Django's built-in system
        django_direct_permissions = list(user.user_permissions.values_list('name', flat=True))
        all_permissions.update(django_direct_permissions)
        
        # Get direct user permissions from custom UserPermission model
        custom_direct_permissions = list(user.userpermission_set.values_list('permission__name', flat=True))
        all_permissions.update(custom_direct_permissions)
        
        # Combine all direct permissions for backward compatibility
        direct_permissions = list(set(django_direct_permissions + custom_direct_permissions))
        
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
            message='Biometric login successful'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['PUT'])
@api_response
def update_biometric_token(request):
    """
    Update user's biometric token
    """
    try:
        user = request.user
        
        # Check if user exists
        if not user or not hasattr(user, 'id'):
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        import json
        data = json.loads(request.body) if request.body else {}
        biometric_token = data.get('biometric_token')
        
        if not biometric_token:
            return error_response(
                message='Biometric token is required',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Update user's biometric token
        user.biometric_token = biometric_token
        user.save()
        
        return success_response(
            message='Biometric token updated successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['DELETE'])
@api_response
def remove_biometric_token(request):
    """
    Remove user's biometric token
    """
    try:
        user = request.user
        
        # Check if user exists
        if not user or not hasattr(user, 'id'):
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Clear user's biometric token
        user.biometric_token = None
        user.save()
        
        return success_response(
            message='Biometric token removed successfully'
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@csrf_exempt
@require_http_methods(["PUT"])
@api_response
def update_profile(request):
    """
    Update user profile including name, phone, and profile picture
    Supports both JSON (when no file) and multipart form data (when file is present)
    """
    try:
        user = request.user
        
        # Check if user exists
        if not user or not hasattr(user, 'id'):
            return error_response(
                message=ERROR_MESSAGES['USER_NOT_FOUND'],
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Parse form fields and files from multipart request
        # Django doesn't populate request.POST or request.FILES for PUT multipart requests automatically
        # We need to manually extract both form fields and files from the multipart data
        name = None
        phone = None
        image_file = None
        
        # Check Content-Type
        content_type = request.META.get('CONTENT_TYPE', '')
        is_multipart = 'multipart/form-data' in content_type
        
        if is_multipart:
            # For multipart PUT requests, try request.POST first (might be populated in some Django versions)
            if request.POST:
                name = request.POST.get('name')
                phone = request.POST.get('phone')
            
            # Try to get file from request.FILES first (in case Django parsed it)
            if 'profile_picture' in request.FILES:
                image_file = request.FILES['profile_picture']
            
            # If POST/FILES are empty, manually parse multipart data in one pass
            if (name is None or phone is None) or (image_file is None and hasattr(request, 'FILES') and not request.FILES):
                try:
                    # Django may have cached the body in _body
                    # Try to get raw body for parsing (only read once)
                    raw_body = None
                    if hasattr(request, '_body') and request._body:
                        raw_body = request._body
                    elif hasattr(request, 'body'):
                        try:
                            raw_body = request.body
                        except:
                            pass
                    
                    if raw_body:
                        import re
                        from io import BytesIO
                        from django.core.files.uploadedfile import InMemoryUploadedFile
                        
                        # Extract boundary from Content-Type
                        boundary_match = re.search(r'boundary=(.+)', content_type)
                        if boundary_match:
                            boundary = boundary_match.group(1).strip().strip('"\'')
                            
                            # Split by boundary
                            parts = raw_body.split(b'--' + boundary.encode())
                            
                            # Parse all parts in one loop (form fields and files)
                            for part in parts:
                                if b'name=' in part:
                                    # Extract field name
                                    name_match = re.search(rb'name="([^"]+)"', part)
                                    if name_match:
                                        field_name = name_match.group(1).decode('utf-8')
                                        
                                        # Check if this is a file field or form field
                                        if b'filename=' in part:
                                            # This is a file field
                                            if field_name == 'profile_picture' and image_file is None:
                                                # Extract filename
                                                filename_match = re.search(rb'filename="([^"]+)"', part)
                                                filename = filename_match.group(1).decode('utf-8', errors='ignore') if filename_match else 'profile_picture.jpg'
                                                
                                                # Extract content-type
                                                content_type_match = re.search(rb'Content-Type:\s*([^\r\n]+)', part)
                                                file_content_type = content_type_match.group(1).decode('utf-8', errors='ignore').strip() if content_type_match else 'image/jpeg'
                                                
                                                # Extract file content (after headers)
                                                if b'\r\n\r\n' in part:
                                                    file_content = part.split(b'\r\n\r\n', 1)[1]
                                                    # Remove trailing boundary markers
                                                    file_content = file_content.split(b'\r\n--')[0].rstrip(b'\r\n')
                                                    
                                                    # Validate file size
                                                    if len(file_content) > FILE_UPLOAD_LIMITS['MAX_FILE_SIZE']:
                                                        return error_response(
                                                            message=f'Image file size exceeds {FILE_UPLOAD_LIMITS["MAX_FILE_SIZE"] // (1024 * 1024)}MB limit',
                                                            status_code=HTTP_STATUS['BAD_REQUEST']
                                                        )
                                                    
                                                    # Validate file type
                                                    if file_content_type not in FILE_UPLOAD_LIMITS['ALLOWED_IMAGE_TYPES']:
                                                        return error_response(
                                                            message='Invalid image file type. Allowed types: jpeg, jpg, png, gif, webp',
                                                            status_code=HTTP_STATUS['BAD_REQUEST']
                                                        )
                                                    
                                                    # Create InMemoryUploadedFile
                                                    file_obj = BytesIO(file_content)
                                                    image_file = InMemoryUploadedFile(
                                                        file_obj,
                                                        'profile_picture',
                                                        filename,
                                                        file_content_type,
                                                        len(file_content),
                                                        'utf-8'
                                                    )
                                        else:
                                            # This is a form field
                                            # Extract field value (between headers and next boundary)
                                            if b'\r\n\r\n' in part:
                                                value_part = part.split(b'\r\n\r\n', 1)[1]
                                                # Remove trailing boundary markers
                                                value_part = value_part.split(b'\r\n--')[0].strip()
                                                
                                                if field_name == 'name' and name is None:
                                                    name = value_part.decode('utf-8', errors='ignore')
                                                elif field_name == 'phone' and phone is None:
                                                    phone = value_part.decode('utf-8', errors='ignore')
                except Exception as parse_error:
                    print(f'Error manually parsing multipart: {parse_error}')
                    import traceback
                    traceback.print_exc()
        else:
            # JSON request
            import json
            try:
                if request.body:
                    data = json.loads(request.body)
                    name = data.get('name')
                    phone = data.get('phone')
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                pass
        
        # Debug logging
        print(f'DEBUG update_profile: name={name}, phone={phone}, image_file={image_file is not None}, content_type={content_type}, has_FILES={bool(request.FILES)}, POST_empty={not (request.POST and request.POST)}')
        
        # Update name if provided
        if name is not None:
            user.name = name.strip() if name else None
        
        # Update phone if provided (with validation)
        if phone is not None:
            new_phone = phone.strip()
            if new_phone:
                # Check if phone is already taken by another user
                if User.objects.filter(phone=new_phone).exclude(id=user.id).exists():
                    return error_response(
                        message='Phone number is already in use',
                        status_code=HTTP_STATUS['BAD_REQUEST']
                    )
                user.phone = new_phone
        
        # Handle profile picture upload
        if image_file:
            # Delete old profile picture if exists
            if user.profile_picture:
                try:
                    if default_storage.exists(user.profile_picture.name):
                        default_storage.delete(user.profile_picture.name)
                except Exception as image_error:
                    print(f'Error deleting old profile picture: {image_error}')
            
            # Set new profile picture
            user.profile_picture = image_file
            
            print(f'DEBUG: Profile picture uploaded - filename={image_file.name}, size={image_file.size}, content_type={image_file.content_type}')
        
        user.save()
        
        # Get updated user roles with permissions
        user_groups = user.groups.all()
        roles_data = []
        all_permissions = set()
        
        for group in user_groups:
            group_permissions = list(group.permissions.values_list('name', flat=True))
            all_permissions.update(group_permissions)
            
            roles_data.append({
                'id': group.id,
                'name': group.name,
                'permissions': group_permissions
            })
        
        # Get direct user permissions
        django_direct_permissions = list(user.user_permissions.values_list('name', flat=True))
        all_permissions.update(django_direct_permissions)
        
        custom_direct_permissions = list(user.userpermission_set.values_list('permission__name', flat=True))
        all_permissions.update(custom_direct_permissions)
        
        direct_permissions = list(set(django_direct_permissions + custom_direct_permissions))
        
        # Get profile picture URL
        profile_picture_url = None
        if user.profile_picture:
            from django.conf import settings
            profile_picture_url = f"{settings.MEDIA_URL}{user.profile_picture.name}"
        
        return success_response(
            data={
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'profilePicture': profile_picture_url,
                'status': 'ACTIVE' if user.is_active else 'INACTIVE',
                'roles': roles_data,
                'permissions': list(all_permissions),
                'directPermissions': direct_permissions,
                'createdAt': user.created_at.isoformat(),
                'updatedAt': user.updated_at.isoformat()
            },
            message='Profile updated successfully'
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(
            message=f"Internal server error: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )