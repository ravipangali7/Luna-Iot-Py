"""
Geofence Vehicle Serializers
Handles serialization for geofence-vehicle relationship endpoints
"""
from rest_framework import serializers
from fleet.models import GeofenceVehicle
from shared.models import Geofence
from fleet.models import Vehicle
from api_common.utils.validation_utils import validate_imei


class GeofenceVehicleSerializer(serializers.ModelSerializer):
    """Serializer for geofence-vehicle relationship model"""
    geofence_title = serializers.CharField(source='geofence.title', read_only=True)
    geofence_type = serializers.CharField(source='geofence.type', read_only=True)
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    vehicle_imei = serializers.CharField(source='vehicle.imei', read_only=True)
    vehicle_no = serializers.CharField(source='vehicle.vehicle_no', read_only=True)
    
    class Meta:
        model = GeofenceVehicle
        fields = [
            'id', 'geofence', 'geofence_title', 'geofence_type', 
            'vehicle', 'vehicle_name', 'vehicle_imei', 'vehicle_no', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class GeofenceVehicleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating geofence-vehicle relationships"""
    geofence_id = serializers.IntegerField(
        help_text="Geofence ID"
    )
    vehicle_imei = serializers.CharField(
        max_length=15,
        help_text="Vehicle IMEI"
    )
    
    class Meta:
        model = GeofenceVehicle
        fields = ['geofence_id', 'vehicle_imei']
    
    def validate_geofence_id(self, value):
        """Validate geofence exists"""
        try:
            Geofence.objects.get(id=value)
        except Geofence.DoesNotExist:
            raise serializers.ValidationError("Geofence with this ID does not exist")
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
        """Validate unique relationship"""
        geofence_id = data.get('geofence_id')
        vehicle_imei = data.get('vehicle_imei')
        
        if GeofenceVehicle.objects.filter(geofence_id=geofence_id, vehicle__imei=vehicle_imei).exists():
            raise serializers.ValidationError("This geofence-vehicle relationship already exists")
        
        return data
    
    def create(self, validated_data):
        """Create geofence-vehicle relationship"""
        geofence_id = validated_data.pop('geofence_id')
        vehicle_imei = validated_data.pop('vehicle_imei')
        
        geofence = Geofence.objects.get(id=geofence_id)
        vehicle = Vehicle.objects.get(imei=vehicle_imei)
        
        return GeofenceVehicle.objects.create(geofence=geofence, vehicle=vehicle)


class GeofenceVehicleListSerializer(serializers.ModelSerializer):
    """Serializer for geofence-vehicle list (minimal data)"""
    geofence_title = serializers.CharField(source='geofence.title', read_only=True)
    geofence_type = serializers.CharField(source='geofence.type', read_only=True)
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    vehicle_imei = serializers.CharField(source='vehicle.imei', read_only=True)
    vehicle_no = serializers.CharField(source='vehicle.vehicle_no', read_only=True)
    
    class Meta:
        model = GeofenceVehicle
        fields = [
            'id', 'geofence_title', 'geofence_type', 'vehicle_name', 
            'vehicle_imei', 'vehicle_no', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class GeofenceVehicleFilterSerializer(serializers.Serializer):
    """Serializer for geofence-vehicle search filters"""
    geofence_id = serializers.IntegerField(
        required=False,
        help_text="Filter by geofence ID"
    )
    vehicle_imei = serializers.CharField(
        required=False,
        help_text="Filter by vehicle IMEI"
    )
    geofence_type = serializers.CharField(
        required=False,
        help_text="Filter by geofence type"
    )
    
    def validate_geofence_id(self, value):
        """Validate geofence exists if provided"""
        if value:
            try:
                Geofence.objects.get(id=value)
            except Geofence.DoesNotExist:
                raise serializers.ValidationError("Geofence with this ID does not exist")
        return value
    
    def validate_vehicle_imei(self, value):
        """Validate IMEI format if provided"""
        if value and not validate_imei(value):
            raise serializers.ValidationError("Invalid IMEI format")
        return value


class VehicleGeofenceAssignmentSerializer(serializers.Serializer):
    """Serializer for assigning geofence to vehicle"""
    geofence_id = serializers.IntegerField(
        help_text="Geofence ID to assign to vehicle"
    )
    
    def validate_geofence_id(self, value):
        """Validate geofence exists"""
        try:
            Geofence.objects.get(id=value)
        except Geofence.DoesNotExist:
            raise serializers.ValidationError("Geofence with this ID does not exist")
        return value


class GeofenceVehicleRemovalSerializer(serializers.Serializer):
    """Serializer for removing geofence from vehicle"""
    geofence_id = serializers.IntegerField(
        help_text="Geofence ID to remove from vehicle"
    )
    
    def validate_geofence_id(self, value):
        """Validate geofence exists"""
        try:
            Geofence.objects.get(id=value)
        except Geofence.DoesNotExist:
            raise serializers.ValidationError("Geofence with this ID does not exist")
        return value


class GeofenceVehicleStatsSerializer(serializers.Serializer):
    """Serializer for geofence-vehicle statistics"""
    total_assignments = serializers.IntegerField()
    geofences_with_vehicles = serializers.IntegerField()
    vehicles_with_geofences = serializers.IntegerField()
    recent_assignments = serializers.IntegerField()
    assignments_by_type = serializers.DictField()