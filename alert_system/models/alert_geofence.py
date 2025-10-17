from django.db import models
from core.models import Institute


class AlertGeofence(models.Model):
    """Model for Alert Geofences"""
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    alert_types = models.ManyToManyField(
        'AlertType',
        blank=True,
        related_name='alert_geofences',
        help_text="Alert types for this geofence"
    )
    boundary = models.JSONField(help_text="GeoJSON boundary data")
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='alert_geofences',
        help_text="Institute this geofence belongs to"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'alert_geofences'
        verbose_name = 'Alert Geofence'
        verbose_name_plural = 'Alert Geofences'
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['institute']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.institute.name})"