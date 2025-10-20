"""
AlarmData Serializers
Handles serialization for alarm data tracking endpoints
"""
from rest_framework import serializers
from device.models import AlarmData, Device
from api_common.utils.validation_utils import validate_imei
from shared_utils.constants import AlarmType


class AlarmDataSerializer(serializers.ModelSerializer):
    """Serializer for alarm data model"""
    imei = serializers.CharField(source='device.imei', read_only=True)
    
    class Meta:
        model = AlarmData
        fields = [
            'id', 'imei', 'latitude', 'longitude', 'speed', 
            'realTimeGps', 'course', 'satellite', 'battery', 
            'signal', 'alarm', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AlarmDataCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alarm data records"""
    imei = serializers.CharField(
        max_length=15,
        help_text="Device IMEI"
    )
    
    class Meta:
        model = AlarmData
        fields = [
            'imei', 'latitude', 'longitude', 'speed', 
            'realTimeGps', 'course', 'satellite', 'battery', 
            'signal', 'alarm'
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
    
    def validate_latitude(self, value):
        """Validate latitude range"""
        if value < -90 or value > 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value
    
    def validate_longitude(self, value):
        """Validate longitude range"""
        if value < -180 or value > 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value
    
    def validate_speed(self, value):
        """Validate speed range"""
        if value < 0 or value > 1000:
            raise serializers.ValidationError("Speed must be between 0 and 1000 km/h")
        return value
    
    def validate_course(self, value):
        """Validate course range"""
        if value < 0 or value > 360:
            raise serializers.ValidationError("Course must be between 0 and 360 degrees")
        return value
    
    def validate_satellite(self, value):
        """Validate satellite count"""
        if value < 0 or value > 50:
            raise serializers.ValidationError("Satellite count must be between 0 and 50")
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
    
    def validate_alarm(self, value):
        """Validate alarm type"""
        if value not in [choice[0] for choice in AlarmType.choices]:
            raise serializers.ValidationError(f"Invalid alarm type. Must be one of: {[choice[0] for choice in AlarmType.choices]}")
        return value
    
    def create(self, validated_data):
        """Create alarm data record"""
        imei = validated_data.pop('imei')
        device = Device.objects.get(imei=imei)
        validated_data['device'] = device
        validated_data['imei'] = imei
        return AlarmData.objects.create(**validated_data)


class AlarmDataListSerializer(serializers.ModelSerializer):
    """Serializer for alarm data list (minimal data)"""
    imei = serializers.CharField(source='device.imei', read_only=True)
    
    class Meta:
        model = AlarmData
        fields = [
            'id', 'imei', 'latitude', 'longitude', 'speed', 
            'alarm', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AlarmDataFilterSerializer(serializers.Serializer):
    """Serializer for alarm data search filters"""
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
    alarm_type = serializers.ChoiceField(
        choices=AlarmType.choices,
        required=False,
        help_text="Filter by alarm type"
    )
    min_speed = serializers.IntegerField(
        required=False,
        help_text="Minimum speed"
    )
    max_speed = serializers.IntegerField(
        required=False,
        help_text="Maximum speed"
    )
    min_latitude = serializers.DecimalField(
        max_digits=12, decimal_places=8,
        required=False,
        help_text="Minimum latitude"
    )
    max_latitude = serializers.DecimalField(
        max_digits=12, decimal_places=8,
        required=False,
        help_text="Maximum latitude"
    )
    min_longitude = serializers.DecimalField(
        max_digits=13, decimal_places=8,
        required=False,
        help_text="Minimum longitude"
    )
    max_longitude = serializers.DecimalField(
        max_digits=13, decimal_places=8,
        required=False,
        help_text="Maximum longitude"
    )
    min_battery = serializers.IntegerField(
        required=False,
        help_text="Minimum battery level"
    )
    max_battery = serializers.IntegerField(
        required=False,
        help_text="Maximum battery level"
    )
    real_time_gps = serializers.BooleanField(
        required=False,
        help_text="Filter by real-time GPS status"
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
        min_speed = data.get('min_speed')
        max_speed = data.get('max_speed')
        min_latitude = data.get('min_latitude')
        max_latitude = data.get('max_latitude')
        min_longitude = data.get('min_longitude')
        max_longitude = data.get('max_longitude')
        min_battery = data.get('min_battery')
        max_battery = data.get('max_battery')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date")
        
        if min_speed is not None and max_speed is not None and min_speed > max_speed:
            raise serializers.ValidationError("Minimum speed must be less than maximum speed")
        
        if min_latitude is not None and max_latitude is not None and min_latitude > max_latitude:
            raise serializers.ValidationError("Minimum latitude must be less than maximum latitude")
        
        if min_longitude is not None and max_longitude is not None and min_longitude > max_longitude:
            raise serializers.ValidationError("Minimum longitude must be less than maximum longitude")
        
        if min_battery is not None and max_battery is not None and min_battery > max_battery:
            raise serializers.ValidationError("Minimum battery must be less than maximum battery")
        
        return data


class AlarmDataStatsSerializer(serializers.Serializer):
    """Serializer for alarm data statistics"""
    total_records = serializers.IntegerField()
    alarm_type_counts = serializers.DictField()
    avg_speed = serializers.DecimalField(max_digits=8, decimal_places=2)
    avg_battery = serializers.DecimalField(max_digits=5, decimal_places=2)
    avg_signal = serializers.DecimalField(max_digits=5, decimal_places=2)
    first_alarm = serializers.DateTimeField()
    last_alarm = serializers.DateTimeField()


class LatestAlarmDataSerializer(serializers.ModelSerializer):
    """Serializer for latest alarm data"""
    imei = serializers.CharField(source='device.imei', read_only=True)
    device_model = serializers.CharField(source='device.model', read_only=True)
    
    class Meta:
        model = AlarmData
        fields = [
            'id', 'imei', 'device_model', 'latitude', 'longitude', 
            'speed', 'realTimeGps', 'course', 'satellite', 'battery', 
            'signal', 'alarm', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
