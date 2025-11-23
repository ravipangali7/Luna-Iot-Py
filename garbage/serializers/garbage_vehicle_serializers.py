"""
Garbage Vehicle Serializers
Handles serialization for garbage vehicle management endpoints
"""
from rest_framework import serializers
from garbage.models import GarbageVehicle
from core.serializers import InstituteSerializer
from fleet.serializers import VehicleSerializer


class GarbageVehicleSerializer(serializers.ModelSerializer):
    """Serializer for garbage vehicle model"""
    institute = InstituteSerializer(read_only=True)
    institute_id = serializers.IntegerField(write_only=True, required=False)
    vehicle = VehicleSerializer(read_only=True)
    vehicle_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = GarbageVehicle
        fields = ['id', 'institute', 'institute_id', 'vehicle', 'vehicle_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class GarbageVehicleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating garbage vehicles"""
    
    class Meta:
        model = GarbageVehicle
        fields = ['institute', 'vehicle']
    
    def validate(self, data):
        """Validate that institute and vehicle combination is unique"""
        institute = data.get('institute')
        vehicle = data.get('vehicle')
        
        if institute and vehicle:
            if GarbageVehicle.objects.filter(institute=institute, vehicle=vehicle).exists():
                raise serializers.ValidationError(
                    "This vehicle is already assigned to this institute"
                )
        
        return data


class GarbageVehicleListSerializer(serializers.ModelSerializer):
    """Serializer for garbage vehicle list (minimal data)"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    vehicle_vehicle_no = serializers.CharField(source='vehicle.vehicleNo', read_only=True)
    
    class Meta:
        model = GarbageVehicle
        fields = ['id', 'institute_name', 'vehicle_name', 'vehicle_vehicle_no', 'created_at']
        read_only_fields = ['id', 'created_at']

