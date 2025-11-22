"""
Vehicle Energy Cost Serializers
Handles serialization for vehicle energy cost management endpoints
"""
from rest_framework import serializers
from fleet.models import VehicleEnergyCost, Vehicle


class VehicleEnergyCostSerializer(serializers.ModelSerializer):
    """Serializer for vehicle energy cost model"""
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    vehicle_imei = serializers.CharField(source='vehicle.imei', read_only=True)
    
    class Meta:
        model = VehicleEnergyCost
        fields = [
            'id', 'vehicle', 'vehicle_name', 'vehicle_imei', 'title', 
            'energy_type', 'entry_date', 'amount', 'total_unit', 
            'remarks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VehicleEnergyCostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating vehicle energy cost records"""
    
    class Meta:
        model = VehicleEnergyCost
        fields = [
            'vehicle', 'title', 'energy_type', 'entry_date', 
            'amount', 'total_unit', 'remarks'
        ]
    
    def validate_energy_type(self, value):
        """Validate energy type"""
        valid_types = ['fuel', 'electric']
        if value not in valid_types:
            raise serializers.ValidationError(f"Energy type must be one of: {', '.join(valid_types)}")
        return value
    
    def validate_amount(self, value):
        """Validate amount"""
        if value < 0:
            raise serializers.ValidationError("Amount cannot be negative")
        return value
    
    def validate_total_unit(self, value):
        """Validate total unit"""
        if value < 0:
            raise serializers.ValidationError("Total unit cannot be negative")
        return value


class VehicleEnergyCostUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating vehicle energy cost records"""
    
    class Meta:
        model = VehicleEnergyCost
        fields = [
            'title', 'energy_type', 'entry_date', 
            'amount', 'total_unit', 'remarks'
        ]
    
    def validate_energy_type(self, value):
        """Validate energy type"""
        valid_types = ['fuel', 'electric']
        if value not in valid_types:
            raise serializers.ValidationError(f"Energy type must be one of: {', '.join(valid_types)}")
        return value
    
    def validate_amount(self, value):
        """Validate amount"""
        if value < 0:
            raise serializers.ValidationError("Amount cannot be negative")
        return value
    
    def validate_total_unit(self, value):
        """Validate total unit"""
        if value < 0:
            raise serializers.ValidationError("Total unit cannot be negative")
        return value


class VehicleEnergyCostListSerializer(serializers.ModelSerializer):
    """Serializer for vehicle energy cost list (minimal data)"""
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    
    class Meta:
        model = VehicleEnergyCost
        fields = [
            'id', 'vehicle', 'vehicle_name', 'title', 'energy_type', 
            'entry_date', 'amount', 'total_unit', 'remarks', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

