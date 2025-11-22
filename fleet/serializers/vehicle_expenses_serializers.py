"""
Vehicle Expenses Serializers
Handles serialization for vehicle expenses management endpoints
"""
from rest_framework import serializers
from fleet.models import VehicleExpenses, Vehicle


class VehicleExpensesSerializer(serializers.ModelSerializer):
    """Serializer for vehicle expenses model"""
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    vehicle_imei = serializers.CharField(source='vehicle.imei', read_only=True)
    
    class Meta:
        model = VehicleExpenses
        fields = [
            'id', 'vehicle', 'vehicle_name', 'vehicle_imei', 'title', 
            'expenses_type', 'entry_date', 'part_expire_month', 'amount', 
            'remarks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VehicleExpensesCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating vehicle expenses records"""
    
    class Meta:
        model = VehicleExpenses
        fields = [
            'vehicle', 'title', 'expenses_type', 'entry_date', 
            'part_expire_month', 'amount', 'remarks'
        ]
    
    def validate_expenses_type(self, value):
        """Validate expenses type"""
        valid_types = ['part', 'fine']
        if value not in valid_types:
            raise serializers.ValidationError(f"Expenses type must be one of: {', '.join(valid_types)}")
        return value
    
    def validate_amount(self, value):
        """Validate amount"""
        if value < 0:
            raise serializers.ValidationError("Amount cannot be negative")
        return value
    
    def validate_part_expire_month(self, value):
        """Validate part expire month"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Part expire month cannot be negative")
        return value


class VehicleExpensesUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating vehicle expenses records"""
    
    class Meta:
        model = VehicleExpenses
        fields = [
            'title', 'expenses_type', 'entry_date', 
            'part_expire_month', 'amount', 'remarks'
        ]
    
    def validate_expenses_type(self, value):
        """Validate expenses type"""
        valid_types = ['part', 'fine']
        if value not in valid_types:
            raise serializers.ValidationError(f"Expenses type must be one of: {', '.join(valid_types)}")
        return value
    
    def validate_amount(self, value):
        """Validate amount"""
        if value < 0:
            raise serializers.ValidationError("Amount cannot be negative")
        return value


class VehicleExpensesListSerializer(serializers.ModelSerializer):
    """Serializer for vehicle expenses list (minimal data)"""
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    
    class Meta:
        model = VehicleExpenses
        fields = [
            'id', 'vehicle', 'vehicle_name', 'title', 'expenses_type', 
            'entry_date', 'amount', 'remarks', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

