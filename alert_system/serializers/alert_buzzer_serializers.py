"""
Alert Buzzer Serializers
Handles serialization for alert buzzer management endpoints
"""
from rest_framework import serializers
from alert_system.models import AlertBuzzer
from core.models import Institute
from device.models import Device


class AlertBuzzerSerializer(serializers.ModelSerializer):
    """Serializer for alert buzzer model"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    alert_geofences = serializers.SerializerMethodField()
    geofences_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertBuzzer
        fields = [
            'id', 'title', 'device', 'device_imei', 'institute', 'institute_name',
            'delay', 'alert_geofences', 'geofences_count', 'created_at', 'updated_at'
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


class AlertBuzzerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alert buzzers"""
    geofence_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of Alert Geofence IDs"
    )
    
    class Meta:
        model = AlertBuzzer
        fields = ['title', 'device', 'institute', 'delay', 'geofence_ids']
    
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
    
    def validate_delay(self, value):
        """Validate delay is positive"""
        if value < 0:
            raise serializers.ValidationError("Delay must be a positive number")
        return value
    
    def create(self, validated_data):
        """Create alert buzzer with geofences"""
        geofence_ids = validated_data.pop('geofence_ids', [])
        
        # Create buzzer
        buzzer = AlertBuzzer.objects.create(**validated_data)
        
        # Assign geofences
        if geofence_ids:
            buzzer.alert_geofences.set(geofence_ids)
        
        return buzzer


class AlertBuzzerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating alert buzzers"""
    geofence_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of Alert Geofence IDs"
    )
    
    class Meta:
        model = AlertBuzzer
        fields = ['title', 'device', 'institute', 'delay', 'geofence_ids']
        extra_kwargs = {
            'title': {'required': False},
            'device': {'required': False},
            'institute': {'required': False},
            'delay': {'required': False}
        }
    
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
    
    def validate_delay(self, value):
        """Validate delay is positive"""
        if value < 0:
            raise serializers.ValidationError("Delay must be a positive number")
        return value
    
    def update(self, instance, validated_data):
        """Update alert buzzer and geofences"""
        geofence_ids = validated_data.pop('geofence_ids', None)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update geofences if provided
        if geofence_ids is not None:
            instance.alert_geofences.set(geofence_ids)
        
        return instance


class AlertBuzzerListSerializer(serializers.ModelSerializer):
    """Serializer for alert buzzer list (minimal data)"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    device_phone = serializers.CharField(source='device.phone', read_only=True)
    geofences_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertBuzzer
        fields = [
            'id', 'title', 'device', 'device_imei', 'device_phone', 'institute', 'institute_name',
            'delay', 'geofences_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_geofences_count(self, obj):
        """Get number of geofences"""
        return obj.alert_geofences.count()
