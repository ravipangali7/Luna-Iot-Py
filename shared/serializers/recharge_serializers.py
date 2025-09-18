"""
Recharge Serializers
Handles serialization for recharge management endpoints
"""
from rest_framework import serializers
from shared.models import Recharge
from device.models import Device
from api_common.utils.validation_utils import validate_imei


class RechargeSerializer(serializers.ModelSerializer):
    """Serializer for recharge model"""
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    device_model = serializers.CharField(source='device.model', read_only=True)
    
    class Meta:
        model = Recharge
        fields = [
            'id', 'device', 'device_imei', 'device_model', 
            'amount', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RechargeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating recharges"""
    device_imei = serializers.CharField(
        max_length=15,
        help_text="Device IMEI"
    )
    
    class Meta:
        model = Recharge
        fields = ['device_imei', 'amount']
    
    def validate_device_imei(self, value):
        """Validate IMEI format and device exists"""
        if not validate_imei(value):
            raise serializers.ValidationError("Invalid IMEI format")
        
        try:
            Device.objects.get(imei=value)
        except Device.DoesNotExist:
            raise serializers.ValidationError("Device with this IMEI does not exist")
        
        return value
    
    def validate_amount(self, value):
        """Validate recharge amount"""
        if value <= 0:
            raise serializers.ValidationError("Recharge amount must be greater than 0")
        
        if value > 10000:
            raise serializers.ValidationError("Recharge amount cannot exceed 10,000")
        
        return value
    
    def create(self, validated_data):
        """Create recharge record"""
        device_imei = validated_data.pop('device_imei')
        device = Device.objects.get(imei=device_imei)
        validated_data['device'] = device
        return Recharge.objects.create(**validated_data)


class RechargeListSerializer(serializers.ModelSerializer):
    """Serializer for recharge list (minimal data)"""
    device_imei = serializers.CharField(source='device.imei', read_only=True)
    device_model = serializers.CharField(source='device.model', read_only=True)
    
    class Meta:
        model = Recharge
        fields = [
            'id', 'device_imei', 'device_model', 
            'amount', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RechargeFilterSerializer(serializers.Serializer):
    """Serializer for recharge search filters"""
    device_imei = serializers.CharField(
        required=False,
        help_text="Filter by device IMEI"
    )
    min_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Minimum recharge amount"
    )
    max_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Maximum recharge amount"
    )
    start_date = serializers.DateTimeField(
        required=False,
        help_text="Start date for filtering"
    )
    end_date = serializers.DateTimeField(
        required=False,
        help_text="End date for filtering"
    )
    
    def validate_device_imei(self, value):
        """Validate IMEI format if provided"""
        if value and not validate_imei(value):
            raise serializers.ValidationError("Invalid IMEI format")
        return value
    
    def validate(self, data):
        """Validate ranges"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        min_amount = data.get('min_amount')
        max_amount = data.get('max_amount')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date")
        
        if min_amount is not None and max_amount is not None and min_amount > max_amount:
            raise serializers.ValidationError("Minimum amount must be less than maximum amount")
        
        return data


class RechargeStatsSerializer(serializers.Serializer):
    """Serializer for recharge statistics"""
    total_recharges = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    min_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    max_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    recent_recharges = serializers.IntegerField()
    devices_recharged = serializers.IntegerField()


class RechargeByDeviceSerializer(serializers.Serializer):
    """Serializer for recharges by device"""
    device_imei = serializers.CharField()
    device_model = serializers.CharField()
    total_recharges = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    last_recharge = serializers.DateTimeField()
    first_recharge = serializers.DateTimeField()


class RechargePaginationSerializer(serializers.Serializer):
    """Serializer for recharge pagination"""
    page = serializers.IntegerField(
        min_value=1,
        help_text="Page number"
    )
    page_size = serializers.IntegerField(
        min_value=1,
        max_value=100,
        help_text="Number of items per page"
    )
    
    def validate_page_size(self, value):
        """Validate page size"""
        if value < 1 or value > 100:
            raise serializers.ValidationError("Page size must be between 1 and 100")
        return value
