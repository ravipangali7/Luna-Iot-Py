"""
Community Siren History Serializers
Handles serialization for community siren history management endpoints
"""
from rest_framework import serializers
from community_siren.models import CommunitySirenHistory
from core.models import Institute
from shared_utils.constants import AlertSource, AlertStatus


class CommunitySirenHistorySerializer(serializers.ModelSerializer):
    """Serializer for community siren history model"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CommunitySirenHistory
        fields = [
            'id', 'source', 'source_display', 'name', 'primary_phone', 'secondary_phone',
            'latitude', 'longitude', 'datetime', 'images', 'remarks', 'status', 'status_display',
            'institute', 'institute_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommunitySirenHistoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating community siren histories"""
    
    class Meta:
        model = CommunitySirenHistory
        fields = [
            'source', 'name', 'primary_phone', 'secondary_phone',
            'latitude', 'longitude', 'datetime', 'images', 'remarks', 'status', 'institute'
        ]
    
    def validate_source(self, value):
        """Validate source is valid choice"""
        valid_sources = ['app', 'switch']
        if value not in valid_sources:
            raise serializers.ValidationError(f"Source must be one of: {', '.join(valid_sources)}")
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
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
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


class CommunitySirenHistoryUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating community siren histories"""
    
    class Meta:
        model = CommunitySirenHistory
        fields = [
            'source', 'name', 'primary_phone', 'secondary_phone',
            'latitude', 'longitude', 'datetime', 'images', 'remarks', 'status'
        ]
    
    def validate_source(self, value):
        """Validate source is valid choice"""
        if value:
            valid_sources = ['app', 'switch']
            if value not in valid_sources:
                raise serializers.ValidationError(f"Source must be one of: {', '.join(valid_sources)}")
        return value
    
    def validate_status(self, value):
        """Validate status is valid choice"""
        if value and value not in [choice[0] for choice in AlertStatus.choices]:
            raise serializers.ValidationError("Invalid status choice")
        return value
    
    def validate_name(self, value):
        """Validate name"""
        if value and not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip() if value else value
    
    def validate_primary_phone(self, value):
        """Validate primary phone"""
        if value and not value.strip():
            raise serializers.ValidationError("Primary phone cannot be empty")
        return value.strip() if value else value
    
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


class CommunitySirenHistoryListSerializer(serializers.ModelSerializer):
    """Serializer for listing community siren histories"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CommunitySirenHistory
        fields = [
            'id', 'source', 'source_display', 'name', 'primary_phone', 'secondary_phone',
            'latitude', 'longitude', 'datetime', 'images', 'remarks', 'status', 'status_display',
            'institute', 'institute_name', 'created_at', 'updated_at'
        ]


class CommunitySirenHistoryStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating community siren history status only"""
    
    class Meta:
        model = CommunitySirenHistory
        fields = ['status']
    
    def validate_status(self, value):
        """Validate status is valid choice"""
        if value not in [choice[0] for choice in AlertStatus.choices]:
            raise serializers.ValidationError("Invalid status choice")
        return value
