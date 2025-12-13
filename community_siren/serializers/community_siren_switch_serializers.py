"""
Community Siren Switch Serializers
Handles serialization for community siren switch management endpoints
"""
from rest_framework import serializers
from community_siren.models import CommunitySirenSwitch
from core.models import Institute
from device.models import Device


class CommunitySirenSwitchSerializer(serializers.ModelSerializer):
    """Serializer for community siren switch model"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    device_phone = serializers.CharField(source='device.phone', read_only=True)
    
    class Meta:
        model = CommunitySirenSwitch
        fields = [
            'id', 'title', 'device', 'device_imei', 'device_phone', 'institute', 'institute_name',
            'latitude', 'longitude', 'trigger', 'primary_phone', 'secondary_phone',
            'image', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommunitySirenSwitchCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating community siren switches"""
    
    class Meta:
        model = CommunitySirenSwitch
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


class CommunitySirenSwitchUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating community siren switches"""
    
    class Meta:
        model = CommunitySirenSwitch
        fields = [
            'title', 'device', 'latitude', 'longitude',
            'trigger', 'primary_phone', 'secondary_phone', 'image'
        ]
    
    def validate_title(self, value):
        """Validate title"""
        if value and not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip() if value else value
    
    def validate_primary_phone(self, value):
        """Validate primary phone"""
        if value and not value.strip():
            raise serializers.ValidationError("Primary phone cannot be empty")
        return value.strip() if value else value
    
    def validate_trigger(self, value):
        """Validate trigger radius is positive"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Trigger radius must be a positive number")
        return value
    
    def validate_latitude(self, value):
        """Validate latitude is within valid range"""
        if value is not None and (value < -90 or value > 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value
    
    def validate_longitude(self, value):
        """Validate longitude is within valid range"""
        if value is not None and (value < -180 or value > 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value


class CommunitySirenSwitchListSerializer(serializers.ModelSerializer):
    """Serializer for listing community siren switches"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    device_phone = serializers.CharField(source='device.phone', read_only=True)
    
    class Meta:
        model = CommunitySirenSwitch
        fields = [
            'id', 'title', 'device', 'device_imei', 'device_phone', 'institute', 'institute_name',
            'latitude', 'longitude', 'trigger', 'primary_phone', 'secondary_phone',
            'image', 'created_at', 'updated_at'
        ]
