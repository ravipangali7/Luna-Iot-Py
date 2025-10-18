"""
Alert Contact Serializers
Handles serialization for alert contact management endpoints
"""
from rest_framework import serializers
from alert_system.models import AlertContact
from core.models import Institute


class AlertContactSerializer(serializers.ModelSerializer):
    """Serializer for alert contact model"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    alert_geofences = serializers.SerializerMethodField()
    alert_types = serializers.SerializerMethodField()
    geofences_count = serializers.SerializerMethodField()
    alert_types_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertContact
        fields = [
            'id', 'name', 'phone', 'institute', 'institute_name',
            'is_sms', 'is_call', 'alert_geofences', 'alert_types',
            'geofences_count', 'alert_types_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'geofences_count', 'alert_types_count']
    
    def get_alert_geofences(self, obj):
        """Get alert geofences with basic info"""
        return [
            {
                'id': geofence.id,
                'title': geofence.title
            }
            for geofence in obj.alert_geofences.all()
        ]
    
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
    
    def get_geofences_count(self, obj):
        """Get number of geofences"""
        return obj.alert_geofences.count()
    
    def get_alert_types_count(self, obj):
        """Get number of alert types"""
        return obj.alert_types.count()


class AlertContactCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alert contacts"""
    geofence_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of Alert Geofence IDs"
    )
    alert_type_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of Alert Type IDs"
    )
    
    class Meta:
        model = AlertContact
        fields = [
            'name', 'phone', 'institute', 'is_sms', 'is_call',
            'geofence_ids', 'alert_type_ids'
        ]
    
    def validate_name(self, value):
        """Validate name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def validate_phone(self, value):
        """Validate phone"""
        if not value or not value.strip():
            raise serializers.ValidationError("Phone cannot be empty")
        return value.strip()
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
        return value
    
    def create(self, validated_data):
        """Create alert contact with geofences and alert types"""
        geofence_ids = validated_data.pop('geofence_ids', [])
        alert_type_ids = validated_data.pop('alert_type_ids', [])
        
        # Create contact
        contact = AlertContact.objects.create(**validated_data)
        
        # Assign geofences and alert types
        if geofence_ids:
            contact.alert_geofences.set(geofence_ids)
        if alert_type_ids:
            contact.alert_types.set(alert_type_ids)
        
        return contact


class AlertContactUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating alert contacts"""
    geofence_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of Alert Geofence IDs"
    )
    alert_type_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of Alert Type IDs"
    )
    
    class Meta:
        model = AlertContact
        fields = [
            'name', 'phone', 'institute', 'is_sms', 'is_call',
            'geofence_ids', 'alert_type_ids'
        ]
        extra_kwargs = {
            'name': {'required': False},
            'phone': {'required': False},
            'institute': {'required': False},
            'is_sms': {'required': False},
            'is_call': {'required': False}
        }
    
    def validate_name(self, value):
        """Validate name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def validate_phone(self, value):
        """Validate phone"""
        if not value or not value.strip():
            raise serializers.ValidationError("Phone cannot be empty")
        return value.strip()
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
        return value
    
    def update(self, instance, validated_data):
        """Update alert contact and relationships"""
        geofence_ids = validated_data.pop('geofence_ids', None)
        alert_type_ids = validated_data.pop('alert_type_ids', None)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update relationships if provided
        if geofence_ids is not None:
            instance.alert_geofences.set(geofence_ids)
        if alert_type_ids is not None:
            instance.alert_types.set(alert_type_ids)
        
        return instance


class AlertContactListSerializer(serializers.ModelSerializer):
    """Serializer for alert contact list (minimal data)"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    alert_geofences_names = serializers.SerializerMethodField()
    alert_types_names = serializers.SerializerMethodField()
    geofences_count = serializers.SerializerMethodField()
    alert_types_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertContact
        fields = [
            'id', 'name', 'phone', 'institute', 'institute_name',
            'is_sms', 'is_call', 'alert_geofences_names', 'alert_types_names',
            'geofences_count', 'alert_types_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_alert_geofences_names(self, obj):
        """Get alert geofence names as list of strings"""
        return [geofence.title for geofence in obj.alert_geofences.all()]
    
    def get_alert_types_names(self, obj):
        """Get alert type names as list of strings"""
        return [alert_type.name for alert_type in obj.alert_types.all()]
    
    def get_geofences_count(self, obj):
        """Get number of geofences"""
        return obj.alert_geofences.count()
    
    def get_alert_types_count(self, obj):
        """Get number of alert types"""
        return obj.alert_types.count()
