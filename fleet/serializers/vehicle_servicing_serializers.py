"""
Vehicle Servicing Serializers
Handles serialization for vehicle servicing management endpoints
"""
from rest_framework import serializers
from fleet.models import VehicleServicing, Vehicle


class VehicleServicingSerializer(serializers.ModelSerializer):
    """Serializer for vehicle servicing model"""
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    vehicle_imei = serializers.CharField(source='vehicle.imei', read_only=True)
    
    class Meta:
        model = VehicleServicing
        fields = [
            'id', 'vehicle', 'vehicle_name', 'vehicle_imei', 'title', 
            'odometer', 'amount', 'date', 'remarks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VehicleServicingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating vehicle servicing records"""
    
    class Meta:
        model = VehicleServicing
        fields = ['vehicle', 'title', 'odometer', 'amount', 'date', 'remarks']
    
    def validate_odometer(self, value):
        """Validate odometer reading"""
        if value < 0:
            raise serializers.ValidationError("Odometer reading cannot be negative")
        return value
    
    def validate_amount(self, value):
        """Validate amount"""
        if value < 0:
            raise serializers.ValidationError("Amount cannot be negative")
        return value


class VehicleServicingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating vehicle servicing records"""
    
    class Meta:
        model = VehicleServicing
        fields = ['title', 'odometer', 'amount', 'date', 'remarks']
    
    def validate_odometer(self, value):
        """Validate odometer reading"""
        if value < 0:
            raise serializers.ValidationError("Odometer reading cannot be negative")
        return value
    
    def validate_amount(self, value):
        """Validate amount"""
        if value < 0:
            raise serializers.ValidationError("Amount cannot be negative")
        return value


class VehicleServicingListSerializer(serializers.ModelSerializer):
    """Serializer for vehicle servicing list (minimal data)"""
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    
    class Meta:
        model = VehicleServicing
        fields = [
            'id', 'vehicle_name', 'title', 'odometer', 'amount', 'date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

