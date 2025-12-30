"""
Device Cart Models
Handles shopping cart functionality for device orders
"""
from django.db import models
from core.models import User
from decimal import Decimal
from .subscription_plan import SubscriptionPlan


class DeviceCart(models.Model):
    """
    Shopping cart for device orders
    One cart per user (one-to-one relationship)
    """
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='device_cart',
        db_column='user_id',
        help_text="User who owns this cart"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'device_carts'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['updated_at']),
        ]

    def __str__(self):
        return f"Cart for {self.user.name or self.user.phone}"

    def get_total_quantity(self):
        """Calculate total quantity of all items in cart"""
        return sum(item.quantity for item in self.items.all())

    def get_subtotal(self):
        """Calculate subtotal of all items in cart"""
        total = sum(item.get_total() for item in self.items.all())
        # Return Decimal(0) if cart is empty, otherwise return the sum
        return total if total else Decimal('0.00')

    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()


class DeviceCartItem(models.Model):
    """
    Individual item in a shopping cart
    """
    id = models.BigAutoField(primary_key=True)
    cart = models.ForeignKey(
        DeviceCart,
        on_delete=models.CASCADE,
        related_name='items',
        db_column='cart_id',
        help_text="Cart this item belongs to"
    )
    subscription_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name='cart_items',
        db_column='subscription_plan_id',
        help_text="Subscription plan being ordered"
    )
    quantity = models.IntegerField(
        default=1,
        help_text="Quantity of devices to order"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price per unit (snapshot of purchasing_price at time of add)"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'device_cart_items'
        ordering = ['created_at']
        unique_together = [['cart', 'subscription_plan']]
        indexes = [
            models.Index(fields=['cart']),
            models.Index(fields=['subscription_plan']),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.subscription_plan.title} in Cart #{self.cart.id}"

    def get_total(self):
        """Calculate total price for this item"""
        return self.price * Decimal(str(self.quantity))

    def save(self, *args, **kwargs):
        """Override save to ensure price is set from subscription plan if not provided"""
        if not self.price and self.subscription_plan:
            self.price = self.subscription_plan.purchasing_price or self.subscription_plan.price
        super().save(*args, **kwargs)

