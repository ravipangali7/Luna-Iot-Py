"""
User Vehicle Serializers
Handles serialization for user-vehicle relationship endpoints
"""
from rest_framework import serializers
from fleet.models import UserVehicle, Vehicle
from core.models import User
from api_common.utils.validation_utils import validate_imei


class UserVehicleSerializer(serializers.ModelSerializer):
    """Serializer for user-vehicle relationship model"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    vehicle_imei = serializers.CharField(source='vehicle.imei', read_only=True)
    vehicle_no = serializers.CharField(source='vehicle.vehicleNo', read_only=True)
    
    class Meta:
        model = UserVehicle
        fields = [
            'id', 'user', 'user_name', 'user_phone', 'vehicle', 'vehicle_name', 
            'vehicle_imei', 'vehicle_no', 'is_main', 'all_access', 'live_tracking', 
            'history', 'report', 'vehicle_profile', 'events', 'geofence', 
            'edit', 'share_tracking', 'notification', 'relay', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserVehicleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user-vehicle relationships"""
    user_id = serializers.IntegerField(
        help_text="User ID"
    )
    vehicle_imei = serializers.CharField(
        max_length=15,
        help_text="Vehicle IMEI"
    )
    
    class Meta:
        model = UserVehicle
        fields = [
            'user_id', 'vehicle_imei', 'is_main', 'all_access', 
            'live_tracking', 'history', 'report', 'vehicle_profile', 
            'events', 'geofence', 'edit', 'share_tracking', 'notification', 'relay'
        ]
    
    def validate_user_id(self, value):
        """Validate user exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this ID does not exist")
        return value
    
    def validate_vehicle_imei(self, value):
        """Validate IMEI format and vehicle exists"""
        if not validate_imei(value):
            raise serializers.ValidationError("Invalid IMEI format")
        
        try:
            Vehicle.objects.get(imei=value)
        except Vehicle.DoesNotExist:
            raise serializers.ValidationError("Vehicle with this IMEI does not exist")
        
        return value
    
    def validate(self, data):
        """Validate unique relationship and permissions"""
        user_id = data.get('user_id')
        vehicle_imei = data.get('vehicle_imei')
        is_main = data.get('is_main', False)
        
        # Check if relationship already exists
        if UserVehicle.objects.filter(user_id=user_id, vehicle__imei=vehicle_imei).exists():
            raise serializers.ValidationError("This user-vehicle relationship already exists")
        
        # If setting as main, ensure no other main vehicle for this user
        if is_main:
            if UserVehicle.objects.filter(user_id=user_id, is_main=True).exists():
                raise serializers.ValidationError("User already has a main vehicle")
        
        return data
    
    def create(self, validated_data):
        """Create user-vehicle relationship"""
        user_id = validated_data.pop('user_id')
        vehicle_imei = validated_data.pop('vehicle_imei')
        
        user = User.objects.get(id=user_id)
        vehicle = Vehicle.objects.get(imei=vehicle_imei)
        
        return UserVehicle.objects.create(user=user, vehicle=vehicle, **validated_data)


class UserVehicleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user-vehicle relationships"""
    
    class Meta:
        model = UserVehicle
        fields = [
            'is_main', 'all_access', 'live_tracking', 'history', 
            'report', 'vehicle_profile', 'events', 'geofence', 
            'edit', 'share_tracking', 'notification', 'relay'
        ]
    
    def validate(self, data):
        """Validate permissions and main vehicle"""
        is_main = data.get('is_main', False)
        user = self.instance.user
        
        # If setting as main, ensure no other main vehicle for this user
        if is_main:
            if UserVehicle.objects.filter(user=user, is_main=True).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("User already has a main vehicle")
        
        return data


class UserVehicleListSerializer(serializers.ModelSerializer):
    """Serializer for user-vehicle list (minimal data)"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    vehicle_imei = serializers.CharField(source='vehicle.imei', read_only=True)
    vehicle_no = serializers.CharField(source='vehicle.vehicleNo', read_only=True)
    
    class Meta:
        model = UserVehicle
        fields = [
            'id', 'user_name', 'user_phone', 'vehicle_name', 
            'vehicle_imei', 'vehicle_no', 'is_main', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserVehicleFilterSerializer(serializers.Serializer):
    """Serializer for user-vehicle search filters"""
    user_id = serializers.IntegerField(
        required=False,
        help_text="Filter by user ID"
    )
    vehicle_imei = serializers.CharField(
        required=False,
        help_text="Filter by vehicle IMEI"
    )
    user_phone = serializers.CharField(
        required=False,
        help_text="Filter by user phone number"
    )
    is_main = serializers.BooleanField(
        required=False,
        help_text="Filter by main vehicle status"
    )
    
    def validate_user_id(self, value):
        """Validate user exists if provided"""
        if value:
            try:
                User.objects.get(id=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("User with this ID does not exist")
        return value
    
    def validate_vehicle_imei(self, value):
        """Validate IMEI format if provided"""
        if value and not validate_imei(value):
            raise serializers.ValidationError("Invalid IMEI format")
        return value


class VehicleAssignmentSerializer(serializers.Serializer):
    """Serializer for assigning vehicle to user"""
    user_id = serializers.IntegerField(
        help_text="User ID to assign vehicle to"
    )
    permissions = serializers.DictField(
        required=False,
        help_text="Vehicle permissions"
    )
    
    def validate_user_id(self, value):
        """Validate user exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this ID does not exist")
        return value


class VehicleRemovalSerializer(serializers.Serializer):
    """Serializer for removing vehicle from user"""
    user_id = serializers.IntegerField(
        help_text="User ID to remove vehicle from"
    )
    
    def validate_user_id(self, value):
        """Validate user exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this ID does not exist")
        return value


class UserVehicleStatsSerializer(serializers.Serializer):
    """Serializer for user-vehicle statistics"""
    total_assignments = serializers.IntegerField()
    main_vehicles = serializers.IntegerField()
    users_with_vehicles = serializers.IntegerField()
    vehicles_with_users = serializers.IntegerField()
    recent_assignments = serializers.IntegerField()
