from django.db import models
from core.models import User
from fleet.models import Vehicle


class GarbageVehicleSubscription(models.Model):
    """Model for Garbage Vehicle Subscriptions"""
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='garbage_vehicle_subscriptions',
        help_text="User who subscribed to the vehicle"
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='garbage_vehicle_subscriptions',
        help_text="Garbage vehicle being subscribed to"
    )
    latitude = models.DecimalField(
        max_digits=18,
        decimal_places=15,
        help_text="User's location latitude for proximity notifications"
    )
    longitude = models.DecimalField(
        max_digits=19,
        decimal_places=15,
        help_text="User's location longitude for proximity notifications"
    )
    notification = models.BooleanField(
        default=True,
        help_text="Whether notifications are enabled for this subscription"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'garbage_vehicle_subscriptions'
        verbose_name = 'Garbage Vehicle Subscription'
        verbose_name_plural = 'Garbage Vehicle Subscriptions'
        unique_together = ['user', 'vehicle']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['vehicle']),
            models.Index(fields=['user', 'vehicle']),
            models.Index(fields=['notification']),
        ]
    
    def __str__(self):
        return f"{self.user.name or self.user.phone} - {self.vehicle.name}"

