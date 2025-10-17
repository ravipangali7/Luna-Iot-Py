"""
Alert Geofence Serializers
Handles serialization for alert geofence management endpoints
"""
from rest_framework import serializers
from alert_system.models import AlertGeofence
from core.models import Institute


class AlertGeofenceSerializer(serializers.ModelSerializer):
    """Serializer for alert geofence model"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    alert_types = serializers.SerializerMethodField()
    alert_types_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertGeofence
        fields = [
            'id', 'title', 'institute', 'institute_name', 'boundary',
            'alert_types', 'alert_types_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'alert_types_count']
    
    def get_alert_types(self, obj):
        """Get alert types with basic info"""
        return [
            {
                'id': alert_type.id,
                'name': alert_type.name,
                'icon': alert_type.icon
            }
            for alert_type in obj.alert_types.all()
        ]
    
    def get_alert_types_count(self, obj):
        """Get number of alert types"""
        return obj.alert_types.count()


class AlertGeofenceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alert geofences"""
    alert_type_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of Alert Type IDs"
    )
    
    class Meta:
        model = AlertGeofence
        fields = ['title', 'institute', 'boundary', 'alert_type_ids']
    
    def validate_title(self, value):
        """Validate title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
        return value
    
    def validate_boundary(self, value):
        """Validate boundary is valid GeoJSON"""
        if not value:
            raise serializers.ValidationError("Boundary is required")
        # Add more GeoJSON validation if needed
        return value
    
    def create(self, validated_data):
        """Create alert geofence with alert types"""
        alert_type_ids = validated_data.pop('alert_type_ids', [])
        
        # Create geofence
        geofence = AlertGeofence.objects.create(**validated_data)
        
        # Assign alert types
        if alert_type_ids:
            geofence.alert_types.set(alert_type_ids)
        
        return geofence


class AlertGeofenceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating alert geofences"""
    alert_type_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of Alert Type IDs"
    )
    
    class Meta:
        model = AlertGeofence
        fields = ['title', 'institute', 'boundary', 'alert_type_ids']
    
    def validate_title(self, value):
        """Validate title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
        return value
    
    def validate_boundary(self, value):
        """Validate boundary is valid GeoJSON"""
        if not value:
            raise serializers.ValidationError("Boundary is required")
        return value
    
    def update(self, instance, validated_data):
        """Update alert geofence and alert types"""
        alert_type_ids = validated_data.pop('alert_type_ids', None)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update alert types if provided
        if alert_type_ids is not None:
            instance.alert_types.set(alert_type_ids)
        
        return instance


class AlertGeofenceListSerializer(serializers.ModelSerializer):
    """Serializer for alert geofence list (minimal data)"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    alert_types_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertGeofence
        fields = [
            'id', 'title', 'institute', 'institute_name',
            'alert_types_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_alert_types_count(self, obj):
        """Get number of alert types"""
        return obj.alert_types.count()
