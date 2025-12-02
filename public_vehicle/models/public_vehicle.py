from django.db import models
from core.models import Institute
from fleet.models import Vehicle


class PublicVehicle(models.Model):
    """Model for Public Vehicle"""
    id = models.BigAutoField(primary_key=True)
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='public_vehicles',
        help_text="Institute this public vehicle belongs to"
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='public_vehicles',
        help_text="Vehicle assigned as public vehicle",
        null=True,
        blank=True,
    )
    description = models.TextField(blank=True, null=True, help_text="Description of the public vehicle")
    is_active = models.BooleanField(default=True, db_column='is_active', help_text="Whether the vehicle is active")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'public_vehicles'
        verbose_name = 'Public Vehicle'
        verbose_name_plural = 'Public Vehicles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['institute']),
            models.Index(fields=['vehicle']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
        unique_together = [['institute', 'vehicle']]
    
    def __str__(self):
        return f"{self.institute.name} - Public Vehicle #{self.id}"

