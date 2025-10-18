"""
Alert Type Serializers
Handles serialization for alert type management endpoints
"""
from rest_framework import serializers
from alert_system.models import AlertType


class AlertTypeSerializer(serializers.ModelSerializer):
    """Serializer for alert type model"""
    
    class Meta:
        model = AlertType
        fields = ['id', 'name', 'icon', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AlertTypeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alert types"""
    
    class Meta:
        model = AlertType
        fields = ['name', 'icon']
    
    def validate_name(self, value):
        """Validate name and check uniqueness"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        
        value = value.strip()
        if AlertType.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Alert type with this name already exists")
        
        return value


class AlertTypeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating alert types"""
    
    class Meta:
        model = AlertType
        fields = ['name', 'icon']
        extra_kwargs = {
            'name': {'required': False},
            'icon': {'required': False}
        }
    
    def validate_name(self, value):
        """Validate name and check uniqueness"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        
        value = value.strip()
        if self.instance and AlertType.objects.filter(name__iexact=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Alert type with this name already exists")
        
        return value


class AlertTypeListSerializer(serializers.ModelSerializer):
    """Serializer for alert type list (minimal data)"""
    
    class Meta:
        model = AlertType
        fields = ['id', 'name', 'icon', 'created_at']
        read_only_fields = ['id', 'created_at']
