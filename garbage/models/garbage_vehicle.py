from django.db import models
from core.models import Institute
from fleet.models import Vehicle


class GarbageVehicle(models.Model):
    """Model for Garbage Vehicle mapping"""
    id = models.BigAutoField(primary_key=True)
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='garbage_vehicles',
        help_text="Institute this garbage vehicle belongs to"
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='garbage_vehicles',
        help_text="Vehicle assigned as garbage vehicle"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'garbage_vehicles'
        verbose_name = 'Garbage Vehicle'
        verbose_name_plural = 'Garbage Vehicles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['institute']),
            models.Index(fields=['vehicle']),
            models.Index(fields=['created_at']),
        ]
        unique_together = [['institute', 'vehicle']]
    
    def __str__(self):
        return f"{self.institute.name} - {self.vehicle.name} ({self.vehicle.vehicleNo})"

