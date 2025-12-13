"""
Community Siren Buzzer Serializers
Handles serialization for community siren buzzer management endpoints
"""
from rest_framework import serializers
from community_siren.models import CommunitySirenBuzzer
from core.models import Institute
from device.models import Device
from device.models.buzzer_status import BuzzerStatus


class CommunitySirenBuzzerSerializer(serializers.ModelSerializer):
    """Serializer for community siren buzzer model"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    device_phone = serializers.CharField(source='device.phone', read_only=True)
    
    class Meta:
        model = CommunitySirenBuzzer
        fields = [
            'id', 'title', 'device', 'device_imei', 'device_phone', 'institute', 'institute_name',
            'delay', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommunitySirenBuzzerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating community siren buzzers"""
    
    class Meta:
        model = CommunitySirenBuzzer
        fields = ['title', 'device', 'institute', 'delay']
    
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
            raise serializers.ValidationError("Delay must be a non-negative number")
        return value


class CommunitySirenBuzzerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating community siren buzzers"""
    
    class Meta:
        model = CommunitySirenBuzzer
        fields = ['title', 'device', 'delay']
    
    def validate_title(self, value):
        """Validate title"""
        if value and not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip() if value else value
    
    def validate_delay(self, value):
        """Validate delay is positive"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Delay must be a non-negative number")
        return value


class CommunitySirenBuzzerListSerializer(serializers.ModelSerializer):
    """Serializer for listing community siren buzzers"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    device_phone = serializers.CharField(source='device.phone', read_only=True)
    
    class Meta:
        model = CommunitySirenBuzzer
        fields = [
            'id', 'title', 'device', 'device_imei', 'device_phone', 'institute', 'institute_name',
            'delay', 'created_at', 'updated_at'
        ]


class CommunitySirenBuzzerWithStatusSerializer(serializers.ModelSerializer):
    """Serializer for community siren buzzer with latest status"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    institute_logo = serializers.CharField(source='institute.logo', read_only=True, allow_null=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    device_phone = serializers.CharField(source='device.phone', read_only=True)
    buzzer_status = serializers.SerializerMethodField()
    
    class Meta:
        model = CommunitySirenBuzzer
        fields = [
            'id', 'title', 'device', 'device_imei', 'device_phone', 'institute', 'institute_name', 'institute_logo',
            'delay', 'buzzer_status', 'created_at', 'updated_at'
        ]
    
    def get_buzzer_status(self, obj):
        """Get latest buzzer status for the device"""
        try:
            latest_status = BuzzerStatus.objects.filter(imei=obj.device.imei).order_by('-createdAt', '-updatedAt').first()
            if latest_status:
                return {
                    'battery': latest_status.battery,
                    'signal': latest_status.signal,
                    'ignition': latest_status.ignition,
                    'charging': latest_status.charging,
                    'relay': latest_status.relay,
                    'last_updated': latest_status.updatedAt.isoformat() if latest_status.updatedAt else None,
                }
        except Exception:
            pass
        return None
