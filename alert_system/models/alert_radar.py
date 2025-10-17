from django.db import models
from core.models import Institute


class AlertRadar(models.Model):
    """Model for Alert Radars"""
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    alert_geofences = models.ManyToManyField(
        'AlertGeofence',
        blank=True,
        related_name='alert_radars',
        help_text="Geofences monitored by this radar"
    )
    token = models.CharField(max_length=500, help_text="Authentication token for radar")
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='alert_radars',
        help_text="Institute this radar belongs to"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'alert_radars'
        verbose_name = 'Alert Radar'
        verbose_name_plural = 'Alert Radars'
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['institute']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.institute.name})"
