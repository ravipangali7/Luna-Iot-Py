"""
Alert Device Serializers
Handles serialization for alert device (buzzer/sos) endpoints
"""
from rest_framework import serializers
from device.models import Device, BuzzerStatus, SosStatus
from shared_utils.constants import DeviceType


class InstituteInfoSerializer(serializers.Serializer):
    """Serializer for institute information"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    logo = serializers.URLField(allow_null=True)


class AlertDeviceStatusSerializer(serializers.Serializer):
    """Serializer for alert device with latest status"""
    id = serializers.CharField()
    imei = serializers.CharField()
    phone = serializers.CharField()
    type = serializers.CharField()
    battery = serializers.IntegerField()
    signal = serializers.IntegerField()
    ignition = serializers.BooleanField()
    charging = serializers.BooleanField()
    relay = serializers.BooleanField()
    lastDataAt = serializers.DateTimeField(source='last_data_at', format='%Y-%m-%dT%H:%M:%S')
    isInactive = serializers.BooleanField()
    statusTable = serializers.CharField(source='status_table')
    institute = InstituteInfoSerializer(allow_null=True)

