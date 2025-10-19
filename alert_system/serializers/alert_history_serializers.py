"""
Alert History Serializers
Handles serialization for alert history management endpoints
"""
from rest_framework import serializers
from alert_system.models import AlertHistory
from core.models import Institute
from shared_utils.constants import AlertSource, AlertStatus


class AlertHistorySerializer(serializers.ModelSerializer):
    """Serializer for alert history model"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    alert_type_name = serializers.CharField(source='alert_type.name', read_only=True)
    alert_type_icon = serializers.CharField(source='alert_type.icon', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = AlertHistory
        fields = [
            'id', 'source', 'source_display', 'name', 'primary_phone', 'secondary_phone',
            'alert_type', 'alert_type_name', 'alert_type_icon', 'latitude', 'longitude',
            'datetime', 'image', 'remarks', 'status', 'status_display',
            'institute', 'institute_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AlertHistoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alert histories"""
    
    class Meta:
        model = AlertHistory
        fields = [
            'source', 'name', 'primary_phone', 'secondary_phone', 'alert_type',
            'latitude', 'longitude', 'datetime', 'image', 'remarks', 'status', 'institute'
        ]
    
    def validate_source(self, value):
        """Validate source is valid choice"""
        if value not in [choice[0] for choice in AlertSource.choices]:
            raise serializers.ValidationError("Invalid source choice")
        return value
    
    def validate_status(self, value):
        """Validate status is valid choice"""
        if value not in [choice[0] for choice in AlertStatus.choices]:
            raise serializers.ValidationError("Invalid status choice")
        return value
    
    def validate_name(self, value):
        """Validate name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def validate_primary_phone(self, value):
        """Validate primary phone"""
        if not value or not value.strip():
            raise serializers.ValidationError("Primary phone cannot be empty")
        return value.strip()
    
    def validate_alert_type(self, value):
        """Validate alert type exists"""
        if not value:
            raise serializers.ValidationError("Alert type is required")
        return value
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
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


class AlertHistoryUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating alert histories"""
    
    class Meta:
        model = AlertHistory
        fields = [
            'source', 'name', 'primary_phone', 'secondary_phone', 'alert_type',
            'latitude', 'longitude', 'datetime', 'image', 'remarks', 'status', 'institute'
        ]
        extra_kwargs = {
            'source': {'required': False},
            'name': {'required': False},
            'primary_phone': {'required': False},
            'secondary_phone': {'required': False},
            'alert_type': {'required': False},
            'latitude': {'required': False},
            'longitude': {'required': False},
            'datetime': {'required': False},
            'image': {'required': False},
            'remarks': {'required': False},
            'status': {'required': False},
            'institute': {'required': False}
        }
    
    def validate_source(self, value):
        """Validate source is valid choice"""
        if value not in [choice[0] for choice in AlertSource.choices]:
            raise serializers.ValidationError("Invalid source choice")
        return value
    
    def validate_status(self, value):
        """Validate status is valid choice"""
        if value not in [choice[0] for choice in AlertStatus.choices]:
            raise serializers.ValidationError("Invalid status choice")
        return value
    
    def validate_name(self, value):
        """Validate name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def validate_primary_phone(self, value):
        """Validate primary phone"""
        if not value or not value.strip():
            raise serializers.ValidationError("Primary phone cannot be empty")
        return value.strip()
    
    def validate_alert_type(self, value):
        """Validate alert type exists"""
        if not value:
            raise serializers.ValidationError("Alert type is required")
        return value
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
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


class AlertHistoryListSerializer(serializers.ModelSerializer):
    """Serializer for alert history list (minimal data)"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    alert_type_name = serializers.CharField(source='alert_type.name', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = AlertHistory
        fields = [
            'id', 'source', 'source_display', 'name', 'primary_phone',
            'alert_type', 'alert_type_name', 'latitude', 'longitude',
            'datetime', 'remarks', 'image', 'status', 'status_display', 'institute', 'institute_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AlertHistoryStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating alert history status only"""
    
    class Meta:
        model = AlertHistory
        fields = ['status', 'remarks']
        extra_kwargs = {
            'status': {'required': False},
            'remarks': {'required': False}
        }
    
    def validate_status(self, value):
        """Validate status is valid choice"""
        if value not in [choice[0] for choice in AlertStatus.choices]:
            raise serializers.ValidationError("Invalid status choice")
        return value
