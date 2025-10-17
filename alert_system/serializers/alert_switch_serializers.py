"""
Alert Switch Serializers
Handles serialization for alert switch management endpoints
"""
from rest_framework import serializers
from alert_system.models import AlertSwitch
from core.models import Institute
from device.models import Device


class AlertSwitchSerializer(serializers.ModelSerializer):
    """Serializer for alert switch model"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    
    class Meta:
        model = AlertSwitch
        fields = [
            'id', 'title', 'device', 'device_imei', 'institute', 'institute_name',
            'latitude', 'longitude', 'trigger', 'primary_phone', 'secondary_phone',
            'image', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AlertSwitchCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alert switches"""
    
    class Meta:
        model = AlertSwitch
        fields = [
            'title', 'device', 'institute', 'latitude', 'longitude',
            'trigger', 'primary_phone', 'secondary_phone', 'image'
        ]
    
    def validate_title(self, value):
        """Validate title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()
    
    def validate_device(self, value):
        """Validate device exists"""
        if not value:
            raise serializers.ValidationError("Device is required")
        return value
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
        return value
    
    def validate_primary_phone(self, value):
        """Validate primary phone"""
        if not value or not value.strip():
            raise serializers.ValidationError("Primary phone cannot be empty")
        return value.strip()
    
    def validate_trigger(self, value):
        """Validate trigger radius is positive"""
        if value <= 0:
            raise serializers.ValidationError("Trigger radius must be a positive number")
        return value
    
    def validate_latitude(self, value):
        """Validate latitude is within valid range"""
        if value < -90 or value > 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value
    
    def validate_longitude(self, value):
        """Validate longitude is within valid range"""
        if value < -180 or value > 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value


class AlertSwitchUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating alert switches"""
    
    class Meta:
        model = AlertSwitch
        fields = [
            'title', 'device', 'institute', 'latitude', 'longitude',
            'trigger', 'primary_phone', 'secondary_phone', 'image'
        ]
    
    def validate_title(self, value):
        """Validate title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()
    
    def validate_device(self, value):
        """Validate device exists"""
        if not value:
            raise serializers.ValidationError("Device is required")
        return value
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
        return value
    
    def validate_primary_phone(self, value):
        """Validate primary phone"""
        if not value or not value.strip():
            raise serializers.ValidationError("Primary phone cannot be empty")
        return value.strip()
    
    def validate_trigger(self, value):
        """Validate trigger radius is positive"""
        if value <= 0:
            raise serializers.ValidationError("Trigger radius must be a positive number")
        return value
    
    def validate_latitude(self, value):
        """Validate latitude is within valid range"""
        if value < -90 or value > 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value
    
    def validate_longitude(self, value):
        """Validate longitude is within valid range"""
        if value < -180 or value > 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value


class AlertSwitchListSerializer(serializers.ModelSerializer):
    """Serializer for alert switch list (minimal data)"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    
    class Meta:
        model = AlertSwitch
        fields = [
            'id', 'title', 'device', 'device_imei', 'institute', 'institute_name',
            'latitude', 'longitude', 'trigger', 'primary_phone', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
