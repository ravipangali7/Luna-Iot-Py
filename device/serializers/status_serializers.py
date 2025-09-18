"""
Status Serializers
Handles serialization for device status tracking endpoints
"""
from rest_framework import serializers
from device.models import Status, Device
from api_common.utils.validation_utils import validate_imei


class StatusSerializer(serializers.ModelSerializer):
    """Serializer for status model"""
    imei = serializers.CharField(source='device.imei', read_only=True)
    
    class Meta:
        model = Status
        fields = [
            'id', 'imei', 'battery', 'signal', 'ignition', 
            'charging', 'relay', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class StatusCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating status records"""
    imei = serializers.CharField(
        max_length=15,
        help_text="Device IMEI"
    )
    
    class Meta:
        model = Status
        fields = [
            'imei', 'battery', 'signal', 'ignition', 
            'charging', 'relay'
        ]
    
    def validate_imei(self, value):
        """Validate IMEI format and device exists"""
        if not validate_imei(value):
            raise serializers.ValidationError("Invalid IMEI format")
        
        try:
            Device.objects.get(imei=value)
        except Device.DoesNotExist:
            raise serializers.ValidationError("Device with this IMEI does not exist")
        
        return value
    
    def validate_battery(self, value):
        """Validate battery percentage"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Battery percentage must be between 0 and 100")
        return value
    
    def validate_signal(self, value):
        """Validate signal strength"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Signal strength must be between 0 and 100")
        return value
    
    def create(self, validated_data):
        """Create status record"""
        imei = validated_data.pop('imei')
        device = Device.objects.get(imei=imei)
        validated_data['device'] = device
        validated_data['imei'] = imei
        return Status.objects.create(**validated_data)


class StatusListSerializer(serializers.ModelSerializer):
    """Serializer for status list (minimal data)"""
    imei = serializers.CharField(source='device.imei', read_only=True)
    
    class Meta:
        model = Status
        fields = [
            'id', 'imei', 'battery', 'signal', 'ignition', 
            'charging', 'relay', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class StatusFilterSerializer(serializers.Serializer):
    """Serializer for status search filters"""
    imei = serializers.CharField(
        required=False,
        help_text="Filter by device IMEI"
    )
    start_date = serializers.DateTimeField(
        required=False,
        help_text="Start date for filtering"
    )
    end_date = serializers.DateTimeField(
        required=False,
        help_text="End date for filtering"
    )
    min_battery = serializers.IntegerField(
        required=False,
        help_text="Minimum battery level"
    )
    max_battery = serializers.IntegerField(
        required=False,
        help_text="Maximum battery level"
    )
    min_signal = serializers.IntegerField(
        required=False,
        help_text="Minimum signal strength"
    )
    max_signal = serializers.IntegerField(
        required=False,
        help_text="Maximum signal strength"
    )
    ignition = serializers.BooleanField(
        required=False,
        help_text="Filter by ignition status"
    )
    charging = serializers.BooleanField(
        required=False,
        help_text="Filter by charging status"
    )
    relay = serializers.BooleanField(
        required=False,
        help_text="Filter by relay status"
    )
    
    def validate_imei(self, value):
        """Validate IMEI format if provided"""
        if value and not validate_imei(value):
            raise serializers.ValidationError("Invalid IMEI format")
        return value
    
    def validate(self, data):
        """Validate ranges"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        min_battery = data.get('min_battery')
        max_battery = data.get('max_battery')
        min_signal = data.get('min_signal')
        max_signal = data.get('max_signal')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date")
        
        if min_battery is not None and max_battery is not None and min_battery > max_battery:
            raise serializers.ValidationError("Minimum battery must be less than maximum battery")
        
        if min_signal is not None and max_signal is not None and min_signal > max_signal:
            raise serializers.ValidationError("Minimum signal must be less than maximum signal")
        
        return data


class StatusStatsSerializer(serializers.Serializer):
    """Serializer for status statistics"""
    total_records = serializers.IntegerField()
    avg_battery = serializers.DecimalField(max_digits=5, decimal_places=2)
    min_battery = serializers.IntegerField()
    max_battery = serializers.IntegerField()
    avg_signal = serializers.DecimalField(max_digits=5, decimal_places=2)
    min_signal = serializers.IntegerField()
    max_signal = serializers.IntegerField()
    ignition_on_count = serializers.IntegerField()
    charging_count = serializers.IntegerField()
    relay_on_count = serializers.IntegerField()
    first_status = serializers.DateTimeField()
    last_status = serializers.DateTimeField()


class LatestStatusSerializer(serializers.ModelSerializer):
    """Serializer for latest status"""
    imei = serializers.CharField(source='device.imei', read_only=True)
    device_model = serializers.CharField(source='device.model', read_only=True)
    
    class Meta:
        model = Status
        fields = [
            'id', 'imei', 'device_model', 'battery', 'signal', 
            'ignition', 'charging', 'relay', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
