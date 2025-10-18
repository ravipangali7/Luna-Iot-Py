"""
Alert Radar Serializers
Handles serialization for alert radar management endpoints
"""
from rest_framework import serializers
from alert_system.models import AlertRadar
from core.models import Institute


class AlertRadarSerializer(serializers.ModelSerializer):
    """Serializer for alert radar model"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    alert_geofences = serializers.SerializerMethodField()
    geofences_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertRadar
        fields = [
            'id', 'title', 'institute', 'institute_name', 'token',
            'alert_geofences', 'geofences_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'geofences_count']
    
    def get_alert_geofences(self, obj):
        """Get alert geofences with basic info"""
        return [
            {
                'id': geofence.id,
                'title': geofence.title
            }
            for geofence in obj.alert_geofences.all()
        ]
    
    def get_geofences_count(self, obj):
        """Get number of geofences"""
        return obj.alert_geofences.count()


class AlertRadarCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alert radars"""
    geofence_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of Alert Geofence IDs"
    )
    
    class Meta:
        model = AlertRadar
        fields = ['title', 'institute', 'token', 'geofence_ids']
        extra_kwargs = {
            'token': {'required': False}
        }
    
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
    
    def validate_token(self, value):
        """Validate token (optional)"""
        if value and not value.strip():
            raise serializers.ValidationError("Token cannot be empty")
        return value.strip() if value else None
    
    def create(self, validated_data):
        """Create alert radar with geofences"""
        geofence_ids = validated_data.pop('geofence_ids', [])
        
        # Generate token if not provided
        if 'token' not in validated_data or not validated_data['token']:
            validated_data['token'] = AlertRadar.generate_token()
        
        # Create radar
        radar = AlertRadar.objects.create(**validated_data)
        
        # Assign geofences
        if geofence_ids:
            radar.alert_geofences.set(geofence_ids)
        
        return radar


class AlertRadarUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating alert radars"""
    geofence_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of Alert Geofence IDs"
    )
    
    class Meta:
        model = AlertRadar
        fields = ['title', 'institute', 'token', 'geofence_ids']
        extra_kwargs = {
            'title': {'required': False},
            'institute': {'required': False},
            'token': {'required': False}
        }
    
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
    
    def validate_token(self, value):
        """Validate token (optional)"""
        if value and not value.strip():
            raise serializers.ValidationError("Token cannot be empty")
        return value.strip() if value else None
    
    def update(self, instance, validated_data):
        """Update alert radar and geofences"""
        geofence_ids = validated_data.pop('geofence_ids', None)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update geofences if provided
        if geofence_ids is not None:
            instance.alert_geofences.set(geofence_ids)
        
        return instance


class AlertRadarListSerializer(serializers.ModelSerializer):
    """Serializer for alert radar list (minimal data)"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    alert_geofences_names = serializers.SerializerMethodField()
    geofences_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertRadar
        fields = [
            'id', 'title', 'institute', 'institute_name',
            'alert_geofences_names', 'geofences_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_alert_geofences_names(self, obj):
        """Get alert geofence names as list of strings"""
        return [geofence.title for geofence in obj.alert_geofences.all()]
    
    def get_geofences_count(self, obj):
        """Get number of geofences"""
        return obj.alert_geofences.count()
