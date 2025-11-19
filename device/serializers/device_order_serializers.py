"""
Device Order Serializers
Handles serialization for device order management endpoints
"""
from rest_framework import serializers
from device.models import DeviceOrder, DeviceOrderItem, SubscriptionPlan
from core.serializers.user_serializers import UserListSerializer


class SubscriptionPlanBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for subscription plan in order items"""
    
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'title', 'price', 'dealer_price', 'purchasing_price']
        read_only_fields = ['id', 'title', 'price', 'dealer_price', 'purchasing_price']


class DeviceOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for device order item"""
    subscription_plan = SubscriptionPlanBasicSerializer(read_only=True)
    subscription_plan_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = DeviceOrderItem
        fields = [
            'id', 'subscription_plan', 'subscription_plan_id',
            'price', 'quantity', 'total', 'created_at'
        ]
        read_only_fields = ['id', 'price', 'total', 'created_at']
    
    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value


class DeviceOrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating device order item"""
    
    class Meta:
        model = DeviceOrderItem
        fields = ['subscription_plan', 'quantity']
    
    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value


class CartItemSerializer(serializers.Serializer):
    """Serializer for cart items (session-based)"""
    subscription_plan_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    subscription_plan_title = serializers.CharField(read_only=True)


class DeviceOrderSerializer(serializers.ModelSerializer):
    """Serializer for device order with items"""
    user_info = serializers.SerializerMethodField()
    items = DeviceOrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = DeviceOrder
        fields = [
            'id', 'user', 'user_info', 'status', 'payment_status',
            'sub_total', 'is_vat', 'vat', 'total',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sub_total', 'vat', 'total', 'created_at', 'updated_at']
    
    def get_user_info(self, obj):
        """Get user information"""
        return UserListSerializer(obj.user).data


class DeviceOrderListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing device orders"""
    user_info = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    
    class Meta:
        model = DeviceOrder
        fields = [
            'id', 'user_info', 'status', 'payment_status',
            'sub_total', 'is_vat', 'vat', 'total',
            'items_count', 'total_quantity', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sub_total', 'vat', 'total', 'created_at', 'updated_at']
    
    def get_user_info(self, obj):
        """Get user information"""
        return UserListSerializer(obj.user).data
    
    def get_items_count(self, obj):
        """Get count of items in order"""
        return obj.items.count()
    
    def get_total_quantity(self, obj):
        """Get total quantity of all items"""
        return sum(item.quantity for item in obj.items.all())


class DeviceOrderCreateSerializer(serializers.Serializer):
    """Serializer for creating device order from cart"""
    items = DeviceOrderItemCreateSerializer(many=True)
    is_vat = serializers.BooleanField(default=False)
    
    def validate_items(self, value):
        """Validate items and minimum quantity"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("Order must have at least one item")
        
        total_quantity = sum(item['quantity'] for item in value)
        if total_quantity < 50:
            raise serializers.ValidationError(
                f"Minimum order quantity is 50 devices. Current total: {total_quantity}"
            )
        
        return value


class DeviceOrderStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating order status"""
    status = serializers.ChoiceField(choices=DeviceOrder.STATUS_CHOICES)
    payment_status = serializers.ChoiceField(
        choices=DeviceOrder.PAYMENT_STATUS_CHOICES,
        required=False
    )

