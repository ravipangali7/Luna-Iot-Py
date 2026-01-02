"""
SIM Balance Serializers
Handles serialization for SIM balance management endpoints
"""
from rest_framework import serializers
from shared.models import SimBalance


class SimBalanceSerializer(serializers.ModelSerializer):
    """Serializer for SIM balance model"""
    device_imei = serializers.CharField(source='device.imei', read_only=True, allow_null=True)
    device_id = serializers.IntegerField(source='device.id', read_only=True, allow_null=True)
    
    class Meta:
        model = SimBalance
        fields = [
            'id', 'device', 'device_id', 'device_imei', 'phone_number', 'state',
            'balance', 'balance_expiry', 'mb', 'remaining_mb', 'mb_expiry_date',
            'last_synced_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_synced_at', 'created_at', 'updated_at']


class SimBalanceListSerializer(serializers.ModelSerializer):
    """Serializer for SIM balance list (minimal data)"""
    device_imei = serializers.CharField(source='device.imei', read_only=True, allow_null=True)
    
    class Meta:
        model = SimBalance
        fields = [
            'id', 'device_imei', 'phone_number', 'state', 'balance',
            'balance_expiry', 'mb', 'remaining_mb', 'mb_expiry_date',
            'last_synced_at', 'created_at'
        ]
        read_only_fields = ['id', 'last_synced_at', 'created_at']


class SimBalanceImportResponseSerializer(serializers.Serializer):
    """Serializer for import response"""
    success = serializers.BooleanField()
    total_rows = serializers.IntegerField()
    successful = serializers.IntegerField()
    failed = serializers.IntegerField()
    errors = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    error = serializers.CharField(required=False)


class SimBalanceFilterSerializer(serializers.Serializer):
    """Serializer for SIM balance search filters"""
    phone_number = serializers.CharField(
        required=False,
        help_text="Filter by phone number"
    )
    state = serializers.CharField(
        required=False,
        help_text="Filter by state (ACTIVE, INACTIVE, etc.)"
    )
    device_id = serializers.IntegerField(
        required=False,
        help_text="Filter by device ID"
    )
    min_balance = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Minimum balance"
    )
    max_balance = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Maximum balance"
    )
    expiry_before = serializers.DateTimeField(
        required=False,
        help_text="Filter by balance expiry before date"
    )
    expiry_after = serializers.DateTimeField(
        required=False,
        help_text="Filter by balance expiry after date"
    )

