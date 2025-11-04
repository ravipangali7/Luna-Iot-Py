"""
Vehicle Serializers
Handles serialization for vehicle management endpoints
"""
from rest_framework import serializers
from fleet.models import Vehicle
from device.models import Device
from api_common.utils.validation_utils import validate_imei


class VehicleSerializer(serializers.ModelSerializer):
    """Serializer for vehicle model"""
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    device_model = serializers.CharField(source='device.model', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'imei', 'device_imei', 'device_model', 'name', 
            'vehicleNo', 'vehicleType', 'odometer', 'mileage', 
            'minimumFuel', 'speedLimit', 'expireDate', 'is_active',
            'createdAt', 'updatedAt'
        ]
        read_only_fields = ['id', 'createdAt', 'updatedAt']


class VehicleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating vehicles"""
    imei = serializers.CharField(
        max_length=15,
        help_text="Device IMEI"
    )
    
    class Meta:
        model = Vehicle
        fields = [
            'imei', 'name', 'vehicleNo', 'vehicleType', 
            'odometer', 'mileage', 'minimumFuel', 'speedLimit', 'expireDate', 'is_active'
        ]
    
    def validate_imei(self, value):
        """Validate IMEI format and device exists"""
        if not validate_imei(value):
            raise serializers.ValidationError("Invalid IMEI format")
        
        try:
            Device.objects.get(imei=value)
        except Device.DoesNotExist:
            raise serializers.ValidationError("Device with this IMEI does not exist")
        
        # Check if vehicle already exists for this IMEI
        if Vehicle.objects.filter(imei=value).exists():
            raise serializers.ValidationError("Vehicle with this IMEI already exists")
        
        return value
    
    def validate_name(self, value):
        """Validate vehicle name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Vehicle name cannot be empty")
        return value.strip()
    
    def validate_vehicleNo(self, value):
        """Validate vehicle number"""
        if not value or not value.strip():
            raise serializers.ValidationError("Vehicle number cannot be empty")
        return value.strip()
    
    def validate_odometer(self, value):
        """Validate odometer reading"""
        if value < 0:
            raise serializers.ValidationError("Odometer reading cannot be negative")
        return value
    
    def validate_mileage(self, value):
        """Validate mileage"""
        if value < 0:
            raise serializers.ValidationError("Mileage cannot be negative")
        return value
    
    def validate_minimumFuel(self, value):
        """Validate minimum fuel level"""
        if value < 0:
            raise serializers.ValidationError("Minimum fuel level cannot be negative")
        return value
    
    def validate_speedLimit(self, value):
        """Validate speed limit"""
        if value < 0 or value > 200:
            raise serializers.ValidationError("Speed limit must be between 0 and 200 km/h")
        return value
    
    def create(self, validated_data):
        """Create vehicle"""
        imei = validated_data.pop('imei')
        device = Device.objects.get(imei=imei)
        validated_data['device'] = device
        validated_data['imei'] = imei
        return Vehicle.objects.create(**validated_data)


class VehicleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating vehicles"""
    
    class Meta:
        model = Vehicle
        fields = [
            'name', 'vehicleNo', 'vehicleType', 'odometer', 
            'mileage', 'minimumFuel', 'speedLimit', 'expireDate', 'is_active'
        ]
    
    def validate_name(self, value):
        """Validate vehicle name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Vehicle name cannot be empty")
        return value.strip()
    
    def validate_vehicleNo(self, value):
        """Validate vehicle number"""
        if not value or not value.strip():
            raise serializers.ValidationError("Vehicle number cannot be empty")
        return value.strip()
    
    def validate_odometer(self, value):
        """Validate odometer reading"""
        if value < 0:
            raise serializers.ValidationError("Odometer reading cannot be negative")
        return value
    
    def validate_mileage(self, value):
        """Validate mileage"""
        if value < 0:
            raise serializers.ValidationError("Mileage cannot be negative")
        return value
    
    def validate_minimumFuel(self, value):
        """Validate minimum fuel level"""
        if value < 0:
            raise serializers.ValidationError("Minimum fuel level cannot be negative")
        return value
    
    def validate_speedLimit(self, value):
        """Validate speed limit"""
        if value < 0 or value > 200:
            raise serializers.ValidationError("Speed limit must be between 0 and 200 km/h")
        return value


class VehicleListSerializer(serializers.ModelSerializer):
    """Serializer for vehicle list (minimal data)"""
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    device_model = serializers.CharField(source='device.model', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'imei', 'device_imei', 'device_model', 
            'name', 'vehicleNo', 'vehicleType', 'is_active', 'createdAt'
        ]
        read_only_fields = ['id', 'createdAt']


class VehicleFilterSerializer(serializers.Serializer):
    """Serializer for vehicle search filters"""
    imei = serializers.CharField(
        required=False,
        help_text="Filter by IMEI"
    )
    vehicle_type = serializers.CharField(
        required=False,
        help_text="Filter by vehicle type"
    )
    name = serializers.CharField(
        required=False,
        help_text="Filter by vehicle name"
    )
    vehicle_no = serializers.CharField(
        required=False,
        help_text="Filter by vehicle number"
    )
    
    def validate_imei(self, value):
        """Validate IMEI format if provided"""
        if value and not validate_imei(value):
            raise serializers.ValidationError("Invalid IMEI format")
        return value


class VehicleAssignmentSerializer(serializers.Serializer):
    """Serializer for vehicle assignment to user"""
    user_id = serializers.IntegerField(
        help_text="User ID to assign vehicle to"
    )
    
    def validate_user_id(self, value):
        """Validate user exists"""
        from core.models import User
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this ID does not exist")
        return value


class VehicleCommandSerializer(serializers.Serializer):
    """Serializer for vehicle commands"""
    command = serializers.CharField(
        max_length=255,
        help_text="Command to send to vehicle"
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


class VehicleStatsSerializer(serializers.Serializer):
    """Serializer for vehicle statistics"""
    total_vehicles = serializers.IntegerField()
    vehicles_by_type = serializers.DictField()
    avg_odometer = serializers.DecimalField(max_digits=10, decimal_places=2)
    avg_mileage = serializers.DecimalField(max_digits=10, decimal_places=2)
    expired_vehicles = serializers.IntegerField()
    active_vehicles = serializers.IntegerField()
    inactive_vehicles = serializers.IntegerField()
