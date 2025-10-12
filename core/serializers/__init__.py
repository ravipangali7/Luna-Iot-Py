"""
Core Serializers Package
Contains all serializers for the core module
"""

from .auth_serializers import *
from .user_serializers import *
from .otp_serializers import *
from .institute_service_serializers import *
from .institute_serializers import *
from .institute_module_serializers import *
__all__ = [
    # Auth serializers
    'LoginSerializer',
    'RegistrationSerializer',
    'OTPVerificationSerializer',
    'ForgotPasswordSerializer',
    'ResetPasswordSerializer',
    
    # User serializers
    'UserSerializer',
    'UserCreateSerializer',
    'UserUpdateSerializer',
    'UserListSerializer',
    
    # OTP serializers
    'OTPSerializer',
    'OTPCreateSerializer',
    
    # Institute Service serializers
    'InstituteServiceSerializer',
    'InstituteServiceCreateSerializer',
    'InstituteServiceUpdateSerializer',
    'InstituteServiceListSerializer',
    
    # Institute serializers
    'InstituteSerializer',
    'InstituteCreateSerializer',
    'InstituteUpdateSerializer',
    'InstituteListSerializer',
    'InstituteLocationSerializer',
    
    # Institute Module serializers
    'InstituteModuleSerializer',
    'InstituteModuleCreateSerializer',
    'InstituteModuleUpdateSerializer',
    'InstituteModuleListSerializer',
    'InstituteModuleUserSerializer',
]
