from django.db import models
from core.models import Institute
from device.models import Device


class AlertSwitch(models.Model):
    """Model for Alert Switches"""
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='alert_switches',
        help_text="Device associated with this switch"
    )
    latitude = models.DecimalField(max_digits=12, decimal_places=8, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=13, decimal_places=8, help_text="Longitude coordinate")
    trigger = models.IntegerField(help_text="Trigger radius in meters")
    primary_phone = models.CharField(max_length=20, help_text="Primary contact phone number")
    secondary_phone = models.CharField(max_length=20, blank=True, null=True, help_text="Secondary contact phone number")
    image = models.ImageField(upload_to='alert_switches/', blank=True, null=True, help_text="Switch image")
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='alert_switches',
        help_text="Institute this switch belongs to"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'alert_switches'
        verbose_name = 'Alert Switch'
        verbose_name_plural = 'Alert Switches'
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['institute']),
            models.Index(fields=['device']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.device.imei})"
