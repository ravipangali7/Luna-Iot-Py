"""
SIM Balance Serializers
Handles serialization for SIM balance management endpoints
"""
from rest_framework import serializers
from shared.models import SimBalance, SimFreeResource, ResourceType


class SimFreeResourceSerializer(serializers.ModelSerializer):
    """Serializer for SIM free resource model"""
    
    class Meta:
        model = SimFreeResource
        fields = [
            'id', 'name', 'resource_type', 'remaining', 'expiry',
            'data_plan_mb', 'remaining_mb',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SimBalanceSerializer(serializers.ModelSerializer):
    """Serializer for SIM balance model with nested free resources"""
    free_resources = SimFreeResourceSerializer(many=True, read_only=True)
    device_imei = serializers.CharField(source='device.imei', read_only=True, allow_null=True)
    device_id = serializers.IntegerField(source='device.id', read_only=True, allow_null=True)
    last_recharge_expiry = serializers.SerializerMethodField()
    last_recharge_remaining_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = SimBalance
        fields = [
            'id', 'device', 'device_id', 'device_imei', 'phone_number', 'state',
            'balance', 'balance_expiry', 'last_recharge_expiry', 'last_recharge_remaining_mb',
            'last_synced_at', 'free_resources',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_synced_at', 'created_at', 'updated_at']
    
    def _get_m2m_50mb_resource(self, obj):
        """Helper method to get m2m 50mb resource with latest expiry"""
        m2m_resources = obj.free_resources.filter(
            name__icontains='m2m',
            name__icontains='50mb',
            resource_type=ResourceType.DATA
        ).order_by('-expiry')
        
        if m2m_resources.exists():
            return m2m_resources.first()
        return None
    
    def get_last_recharge_expiry(self, obj):
        """Get expiry from m2m 50mb resource with latest expiry"""
        resource = self._get_m2m_50mb_resource(obj)
        if resource:
            return resource.expiry
        return None
    
    def get_last_recharge_remaining_mb(self, obj):
        """Get remaining MB from m2m 50mb resource with latest expiry"""
        resource = self._get_m2m_50mb_resource(obj)
        if resource and resource.remaining_mb is not None:
            return resource.remaining_mb
        return None


class SimBalanceListSerializer(serializers.ModelSerializer):
    """Serializer for SIM balance list (minimal data)"""
    device_imei = serializers.CharField(source='device.imei', read_only=True, allow_null=True)
    free_resources_count = serializers.SerializerMethodField()
    last_recharge_expiry = serializers.SerializerMethodField()
    last_recharge_remaining_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = SimBalance
        fields = [
            'id', 'device_imei', 'phone_number', 'state', 'balance',
            'balance_expiry', 'last_recharge_expiry', 'last_recharge_remaining_mb',
            'free_resources_count', 'last_synced_at', 'created_at'
        ]
        read_only_fields = ['id', 'last_synced_at', 'created_at']
    
    def get_free_resources_count(self, obj):
        """Get count of free resources"""
        return obj.free_resources.count()
    
    def _get_m2m_50mb_resource(self, obj):
        """Helper method to get m2m 50mb resource with latest expiry"""
        m2m_resources = obj.free_resources.filter(
            name__icontains='m2m',
            name__icontains='50mb',
            resource_type=ResourceType.DATA
        ).order_by('-expiry')
        
        if m2m_resources.exists():
            return m2m_resources.first()
        return None
    
    def get_last_recharge_expiry(self, obj):
        """Get expiry from m2m 50mb resource with latest expiry"""
        resource = self._get_m2m_50mb_resource(obj)
        if resource:
            return resource.expiry
        return None
    
    def get_last_recharge_remaining_mb(self, obj):
        """Get remaining MB from m2m 50mb resource with latest expiry"""
        resource = self._get_m2m_50mb_resource(obj)
        if resource and resource.remaining_mb is not None:
            return resource.remaining_mb
        return None


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

