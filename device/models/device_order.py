from django.db import models
from core.models import User
from decimal import Decimal
from .subscription_plan import SubscriptionPlan


class DeviceOrder(models.Model):
    """Device Order model for tracking device orders from dealers"""
    
    STATUS_CHOICES = [
        ('accepted', 'Accepted'),
        ('preparing', 'Preparing'),
        ('dispatch', 'Dispatch'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('completed', 'Completed'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='device_orders',
        db_column='user_id',
        help_text="User who placed the order"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='accepted',
        db_column='status',
        help_text="Order status"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        db_column='payment_status',
        help_text="Payment status"
    )
    sub_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_column='sub_total',
        help_text="Subtotal amount before VAT"
    )
    is_vat = models.BooleanField(
        default=False,
        db_column='is_vat',
        help_text="Whether VAT is applicable"
    )
    vat = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        db_column='vat',
        help_text="VAT amount (13%)"
    )
    total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_column='total',
        help_text="Total amount including VAT"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_column='created_at',
        help_text="Order creation timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_column='updated_at',
        help_text="Last order update timestamp"
    )
    
    class Meta:
        db_table = 'device_orders'
        verbose_name = 'Device Order'
        verbose_name_plural = 'Device Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.name or self.user.phone} - {self.total}"
    
    def calculate_totals(self):
        """Calculate VAT and total based on subtotal and is_vat flag"""
        self.sub_total = sum(item.total for item in self.items.all())
        
        if self.is_vat:
            # Calculate 13% VAT
            self.vat = self.sub_total * Decimal('0.13')
        else:
            self.vat = Decimal('0.00')
        
        self.total = self.sub_total + self.vat
        self.save()


class DeviceOrderItem(models.Model):
    """Device Order Item model for individual items in an order"""
    
    id = models.BigAutoField(primary_key=True)
    device_order = models.ForeignKey(
        DeviceOrder,
        on_delete=models.CASCADE,
        related_name='items',
        db_column='device_order_id',
        help_text="The device order this item belongs to"
    )
    subscription_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name='order_items',
        db_column='subscription_plan_id',
        help_text="Subscription plan (device product) for this order item"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_column='price',
        help_text="Price per unit (purchasing_price from subscription plan)"
    )
    quantity = models.IntegerField(
        db_column='quantity',
        help_text="Quantity of devices ordered"
    )
    total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_column='total',
        help_text="Total amount (price * quantity)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_column='created_at',
        help_text="Item creation timestamp"
    )
    
    class Meta:
        db_table = 'device_order_items'
        verbose_name = 'Device Order Item'
        verbose_name_plural = 'Device Order Items'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['device_order']),
            models.Index(fields=['subscription_plan']),
        ]
    
    def __str__(self):
        return f"Order Item {self.id} - {self.subscription_plan.title} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        """Calculate total before saving"""
        self.total = self.price * Decimal(str(self.quantity))
        super().save(*args, **kwargs)
        
        # Recalculate order totals after saving item
        if self.device_order:
            self.device_order.calculate_totals()

