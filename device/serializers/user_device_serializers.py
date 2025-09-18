"""
User Device Serializers
Handles serialization for user-device relationship endpoints
"""
from rest_framework import serializers
from device.models import UserDevice, Device
from core.models import User
from api_common.utils.validation_utils import validate_imei


class UserDeviceSerializer(serializers.ModelSerializer):
    """Serializer for user-device relationship model"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    device_model = serializers.CharField(source='device.model', read_only=True)
    
    class Meta:
        model = UserDevice
        fields = [
            'id', 'user', 'user_name', 'user_phone', 
            'device', 'device_imei', 'device_model', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserDeviceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user-device relationships"""
    user_id = serializers.IntegerField(
        help_text="User ID"
    )
    device_imei = serializers.CharField(
        max_length=15,
        help_text="Device IMEI"
    )
    
    class Meta:
        model = UserDevice
        fields = ['user_id', 'device_imei']
    
    def validate_user_id(self, value):
        """Validate user exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this ID does not exist")
        return value
    
    def validate_device_imei(self, value):
        """Validate IMEI format and device exists"""
        if not validate_imei(value):
            raise serializers.ValidationError("Invalid IMEI format")
        
        try:
            Device.objects.get(imei=value)
        except Device.DoesNotExist:
            raise serializers.ValidationError("Device with this IMEI does not exist")
        
        return value
    
    def validate(self, data):
        """Validate unique relationship"""
        user_id = data.get('user_id')
        device_imei = data.get('device_imei')
        
        if UserDevice.objects.filter(user_id=user_id, device__imei=device_imei).exists():
            raise serializers.ValidationError("This user-device relationship already exists")
        
        return data
    
    def create(self, validated_data):
        """Create user-device relationship"""
        user_id = validated_data.pop('user_id')
        device_imei = validated_data.pop('device_imei')
        
        user = User.objects.get(id=user_id)
        device = Device.objects.get(imei=device_imei)
        
        return UserDevice.objects.create(user=user, device=device)


class UserDeviceListSerializer(serializers.ModelSerializer):
    """Serializer for user-device list (minimal data)"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    device_model = serializers.CharField(source='device.model', read_only=True)
    
    class Meta:
        model = UserDevice
        fields = [
            'id', 'user_name', 'user_phone', 
            'device_imei', 'device_model', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserDeviceFilterSerializer(serializers.Serializer):
    """Serializer for user-device search filters"""
    user_id = serializers.IntegerField(
        required=False,
        help_text="Filter by user ID"
    )
    device_imei = serializers.CharField(
        required=False,
        help_text="Filter by device IMEI"
    )
    user_phone = serializers.CharField(
        required=False,
        help_text="Filter by user phone number"
    )
    
    def validate_user_id(self, value):
        """Validate user exists if provided"""
        if value:
            try:
                User.objects.get(id=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("User with this ID does not exist")
        return value
    
    def validate_device_imei(self, value):
        """Validate IMEI format if provided"""
        if value and not validate_imei(value):
            raise serializers.ValidationError("Invalid IMEI format")
        return value


class DeviceAssignmentSerializer(serializers.Serializer):
    """Serializer for assigning device to user"""
    user_id = serializers.IntegerField(
        help_text="User ID to assign device to"
    )
    
    def validate_user_id(self, value):
        """Validate user exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this ID does not exist")
        return value


class DeviceRemovalSerializer(serializers.Serializer):
    """Serializer for removing device from user"""
    user_id = serializers.IntegerField(
        help_text="User ID to remove device from"
    )
    
    def validate_user_id(self, value):
        """Validate user exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this ID does not exist")
        return value


class UserDeviceStatsSerializer(serializers.Serializer):
    """Serializer for user-device statistics"""
    total_assignments = serializers.IntegerField()
    active_devices = serializers.IntegerField()
    users_with_devices = serializers.IntegerField()
    devices_with_users = serializers.IntegerField()
    recent_assignments = serializers.IntegerField()