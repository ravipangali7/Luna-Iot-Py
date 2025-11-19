"""
Device Order Serializers
Handles serialization for device order management endpoints
"""
from rest_framework import serializers
from device.models import DeviceOrder, DeviceOrderItem, SubscriptionPlan, DeviceCart, DeviceCartItem
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
    price = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    
    class Meta:
        model = DeviceOrderItem
        fields = [
            'id', 'subscription_plan', 'subscription_plan_id',
            'price', 'quantity', 'total', 'created_at'
        ]
        read_only_fields = ['id', 'price', 'total', 'created_at']
    
    def get_price(self, obj):
        """Convert price to float"""
        return float(obj.price)
    
    def get_total(self, obj):
        """Convert total to float"""
        return float(obj.total)
    
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


class DeviceCartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items (database model)"""
    subscription_plan_id = serializers.IntegerField(source='subscription_plan.id', read_only=True)
    subscription_plan_title = serializers.CharField(source='subscription_plan.title', read_only=True)
    price = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    
    class Meta:
        model = DeviceCartItem
        fields = [
            'id', 'subscription_plan_id', 'subscription_plan_title',
            'price', 'quantity', 'total', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'price', 'total', 'created_at', 'updated_at']
    
    def get_price(self, obj):
        """Convert price to float"""
        return float(obj.price)
    
    def get_total(self, obj):
        """Calculate total for cart item"""
        return float(obj.get_total())


class DeviceCartSerializer(serializers.ModelSerializer):
    """Serializer for device cart with items"""
    items = DeviceCartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DeviceCart
        fields = ['id', 'items', 'subtotal', 'total_quantity', 'item_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_subtotal(self, obj):
        """Calculate subtotal of all items"""
        return float(obj.get_subtotal())
    
    def get_total_quantity(self, obj):
        """Calculate total quantity"""
        return obj.get_total_quantity()
    
    def get_item_count(self, obj):
        """Get count of items in cart"""
        return obj.items.count()


class CartItemSerializer(serializers.Serializer):
    """Legacy serializer for cart items (kept for compatibility)"""
    subscription_plan_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    subscription_plan_title = serializers.CharField(read_only=True)


class DeviceOrderSerializer(serializers.ModelSerializer):
    """Serializer for device order with items"""
    user_info = serializers.SerializerMethodField()
    items = DeviceOrderItemSerializer(many=True, read_only=True)
    sub_total = serializers.SerializerMethodField()
    vat = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    
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
    
    def get_sub_total(self, obj):
        """Convert sub_total to float"""
        return float(obj.sub_total)
    
    def get_vat(self, obj):
        """Convert vat to float"""
        return float(obj.vat)
    
    def get_total(self, obj):
        """Convert total to float"""
        return float(obj.total)


class DeviceOrderListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing device orders"""
    user_info = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    sub_total = serializers.SerializerMethodField()
    vat = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    
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
    
    def get_sub_total(self, obj):
        """Convert sub_total to float"""
        return float(obj.sub_total)
    
    def get_vat(self, obj):
        """Convert vat to float"""
        return float(obj.vat)
    
    def get_total(self, obj):
        """Convert total to float"""
        return float(obj.total)
    
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

