"""
Device Serializers
Handles serialization for device management endpoints
"""
from rest_framework import serializers
from device.models import Device
from api_common.utils.validation_utils import validate_imei


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for device model"""
    
    class Meta:
        model = Device
        fields = [
            'id', 'imei', 'phone', 'sim', 'protocol', 
            'iccid', 'model', 'subscription_plan', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DeviceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating devices"""
    
    class Meta:
        model = Device
        fields = [
            'imei', 'phone', 'sim', 'protocol', 
            'iccid', 'model', 'subscription_plan'
        ]
    
    def validate_imei(self, value):
        """Validate IMEI format"""
        if not validate_imei(value):
            raise serializers.ValidationError("Invalid IMEI format")
        
        # Check if IMEI already exists
        if Device.objects.filter(imei=value).exists():
            raise serializers.ValidationError("Device with this IMEI already exists")
        
        return value
    
    def validate_phone(self, value):
        """Validate phone number"""
        if not value or not value.strip():
            raise serializers.ValidationError("Phone number cannot be empty")
        return value.strip()


class DeviceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating devices"""
    
    class Meta:
        model = Device
        fields = [
            'phone', 'sim', 'protocol', 'iccid', 'model', 'subscription_plan'
        ]
    
    def validate_phone(self, value):
        """Validate phone number"""
        if not value or not value.strip():
            raise serializers.ValidationError("Phone number cannot be empty")
        return value.strip()


class DeviceListSerializer(serializers.ModelSerializer):
    """Serializer for device list (minimal data)"""
     
    class Meta:
        model = Device
        fields = [
            'id', 'imei', 'phone', 'sim', 'protocol', 
            'model', 'subscription_plan', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DeviceAssignmentSerializer(serializers.Serializer):
    """Serializer for device assignment to user"""
    user_id = serializers.IntegerField(
        help_text="User ID to assign device to"
    )
    
    def validate_user_id(self, value):
        """Validate user exists"""
        from core.models import User
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this ID does not exist")
        return value


class DeviceCommandSerializer(serializers.Serializer):
    """Serializer for device commands"""
    command = serializers.CharField(
        max_length=255,
        help_text="Command to send to device"
    )
    parameters = serializers.JSONField(
        required=False,
        help_text="Command parameters"
    )
    
    def validate_command(self, value):
        """Validate command"""
        if not value or not value.strip():
            raise serializers.ValidationError("Command cannot be empty")
        return value.strip()


class DeviceSearchSerializer(serializers.Serializer):
    """Serializer for device search filters"""
    imei = serializers.CharField(
        required=False,
        help_text="Filter by IMEI"
    )
    phone = serializers.CharField(
        required=False,
        help_text="Filter by phone number"
    )
    sim = serializers.CharField(
        required=False,
        help_text="Filter by SIM type"
    )
    protocol = serializers.CharField(
        required=False,
        help_text="Filter by protocol"
    )
    model = serializers.CharField(
        required=False,
        help_text="Filter by device model"
    )
    
    def validate_imei(self, value):
        """Validate IMEI format if provided"""
        if value and not validate_imei(value):
            raise serializers.ValidationError("Invalid IMEI format")
        return value
