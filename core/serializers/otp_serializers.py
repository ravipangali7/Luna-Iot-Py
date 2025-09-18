"""
OTP Serializers
Handles serialization for OTP-related endpoints
"""
from rest_framework import serializers
from core.models import Otp
from api_common.utils.validation_utils import validate_phone_number


class OTPSerializer(serializers.ModelSerializer):
    """Serializer for OTP model"""
    
    class Meta:
        model = Otp
        fields = ['id', 'phone', 'otp', 'expires_at', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if not validate_phone_number(value):
            raise serializers.ValidationError("Invalid phone number format")
        return value.strip()


class OTPCreateSerializer(serializers.Serializer):
    """Serializer for creating OTP"""
    phone = serializers.CharField(
        max_length=100,
        help_text="Phone number to send OTP to"
    )
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if not validate_phone_number(value):
            raise serializers.ValidationError("Invalid phone number format")
        return value.strip()


class OTPVerificationSerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    phone = serializers.CharField(
        max_length=100,
        help_text="Phone number"
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
    
    def validate_otp(self, value):
        """Validate OTP format"""
        if not value or len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError("OTP must be a 6-digit number")
        return value


class OTPResponseSerializer(serializers.Serializer):
    """Serializer for OTP response"""
    phone = serializers.CharField()
    message = serializers.CharField()
    expires_in_minutes = serializers.IntegerField()


class OTPListSerializer(serializers.ModelSerializer):
    """Serializer for OTP list (minimal data)"""
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Otp
        fields = ['id', 'phone', 'is_expired', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_is_expired(self, obj):
        """Check if OTP is expired"""
        return obj.is_expired()
