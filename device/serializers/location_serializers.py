"""
Location Serializers
Handles serialization for location tracking endpoints
"""
from rest_framework import serializers
from device.models import Location, Device
from api_common.utils.validation_utils import validate_imei


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for location model"""
    imei = serializers.CharField(source='device.imei', read_only=True)
    
    class Meta:
        model = Location
        fields = [
            'id', 'imei', 'latitude', 'longitude', 'speed', 
            'course', 'real_time_gps', 'satellite', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LocationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating location records"""
    imei = serializers.CharField(
        max_length=15,
        help_text="Device IMEI"
    )
    
    class Meta:
        model = Location
        fields = [
            'imei', 'latitude', 'longitude', 'speed', 
            'course', 'real_time_gps', 'satellite'
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
        if value < 0:
            raise serializers.ValidationError("Speed cannot be negative")
        return value
    
    def validate_course(self, value):
        """Validate course range"""
        if value < 0 or value > 360:
            raise serializers.ValidationError("Course must be between 0 and 360")
        return value
    
    def validate_satellite(self, value):
        """Validate satellite count"""
        if value < 0:
            raise serializers.ValidationError("Satellite count cannot be negative")
        return value
    
    def create(self, validated_data):
        """Create location record"""
        imei = validated_data.pop('imei')
        device = Device.objects.get(imei=imei)
        validated_data['device'] = device
        validated_data['imei'] = imei
        return Location.objects.create(**validated_data)


class LocationListSerializer(serializers.ModelSerializer):
    """Serializer for location list (minimal data)"""
    imei = serializers.CharField(source='device.imei', read_only=True)
    
    class Meta:
        model = Location
        fields = [
            'id', 'imei', 'latitude', 'longitude', 
            'speed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LocationFilterSerializer(serializers.Serializer):
    """Serializer for location search filters"""
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
    min_speed = serializers.IntegerField(
        required=False,
        help_text="Minimum speed filter"
    )
    max_speed = serializers.IntegerField(
        required=False,
        help_text="Maximum speed filter"
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
        """Validate date range"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date")
        
        return data


class LocationReportSerializer(serializers.Serializer):
    """Serializer for location report generation"""
    imei = serializers.CharField(
        help_text="Device IMEI"
    )
    start_date = serializers.DateTimeField(
        help_text="Start date for report"
    )
    end_date = serializers.DateTimeField(
        help_text="End date for report"
    )
    report_type = serializers.ChoiceField(
        choices=[
            ('summary', 'Summary Report'),
            ('detailed', 'Detailed Report'),
            ('speed', 'Speed Analysis'),
            ('route', 'Route Analysis')
        ],
        help_text="Type of report to generate"
    )
    
    def validate_imei(self, value):
        """Validate IMEI format and device exists"""
        if not validate_imei(value):
            raise serializers.ValidationError("Invalid IMEI format")
        
        try:
            Device.objects.get(imei=value)
        except Device.DoesNotExist:
            raise serializers.ValidationError("Device with this IMEI does not exist")
        
        return value
    
    def validate(self, data):
        """Validate date range"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date")
        
        return data


class LocationStatsSerializer(serializers.Serializer):
    """Serializer for location statistics"""
    total_locations = serializers.IntegerField()
    avg_speed = serializers.DecimalField(max_digits=5, decimal_places=2)
    max_speed = serializers.IntegerField()
    total_distance = serializers.DecimalField(max_digits=10, decimal_places=2)
    first_location = serializers.DateTimeField()
    last_location = serializers.DateTimeField()
