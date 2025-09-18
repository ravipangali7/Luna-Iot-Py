"""
Authentication Serializers
Handles serialization for authentication-related endpoints
"""
from rest_framework import serializers
from core.models import User, Otp
from api_common.utils.validation_utils import validate_phone_number


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    phone = serializers.CharField(
        max_length=100,
        help_text="User's phone number"
    )
    password = serializers.CharField(
        max_length=255,
        help_text="User's password"
    )
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if not validate_phone_number(value):
            raise serializers.ValidationError("Invalid phone number format")
        return value.strip()


class RegistrationSerializer(serializers.Serializer):
    """Serializer for user registration"""
    name = serializers.CharField(
        max_length=100,
        help_text="User's full name"
    )
    phone = serializers.CharField(
        max_length=100,
        help_text="User's phone number"
    )
    password = serializers.CharField(
        min_length=6,
        max_length=255,
        help_text="User's password (minimum 6 characters)"
    )
    otp = serializers.CharField(
        max_length=6,
        help_text="OTP verification code"
    )
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if not validate_phone_number(value):
            raise serializers.ValidationError("Invalid phone number format")
        return value.strip()
    
    def validate_name(self, value):
        """Validate name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def validate_password(self, value):
        """Validate password strength"""
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long")
        return value


class OTPVerificationSerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    phone = serializers.CharField(
        max_length=100,
        help_text="User's phone number"
    )
    otp = serializers.CharField(
        max_length=6,
        help_text="OTP verification code"
    )
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if not validate_phone_number(value):
            raise serializers.ValidationError("Invalid phone number format")
        return value.strip()


class SendOTPSerializer(serializers.Serializer):
    """Serializer for sending OTP"""
    phone = serializers.CharField(
        max_length=100,
        help_text="User's phone number"
    )
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if not validate_phone_number(value):
            raise serializers.ValidationError("Invalid phone number format")
        return value.strip()


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password OTP verification"""
    phone = serializers.CharField(
        max_length=100,
        help_text="User's phone number"
    )
    otp = serializers.CharField(
        max_length=6,
        help_text="OTP verification code"
    )
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if not validate_phone_number(value):
            raise serializers.ValidationError("Invalid phone number format")
        return value.strip()


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for password reset"""
    phone = serializers.CharField(
        max_length=100,
        help_text="User's phone number"
    )
    reset_token = serializers.CharField(
        max_length=255,
        help_text="Reset token from OTP verification"
    )
    new_password = serializers.CharField(
        min_length=6,
        max_length=255,
        help_text="New password (minimum 6 characters)"
    )
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if not validate_phone_number(value):
            raise serializers.ValidationError("Invalid phone number format")
        return value.strip()
    
    def validate_new_password(self, value):
        """Validate new password strength"""
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long")
        return value


class UserResponseSerializer(serializers.ModelSerializer):
    """Serializer for user response data"""
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'name', 'phone', 'is_active', 'roles', 
            'permissions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_roles(self, obj):
        """Get user's groups (roles) with their permissions"""
        groups_data = []
        for group in obj.groups.all():
            group_data = {
                'id': group.id,
                'name': group.name,
                'permissions': list(group.permissions.values_list('name', flat=True))
            }
            groups_data.append(group_data)
        return groups_data
    
    def get_permissions(self, obj):
        """Get user's combined permissions (group + direct)"""
        # Get group permissions
        group_permissions = []
        for group in obj.groups.all():
            group_permissions.extend(group.permissions.values_list('name', flat=True))
        
        # Get direct permissions
        direct_permissions = list(obj.user_permissions.values_list('name', flat=True))
        
        # Combine and deduplicate
        return list(set(group_permissions + direct_permissions))


class LoginResponseSerializer(serializers.Serializer):
    """Serializer for login response"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    phone = serializers.CharField()
    token = serializers.CharField()
    roles = serializers.ListField(child=serializers.DictField())
    permissions = serializers.ListField(child=serializers.CharField())
