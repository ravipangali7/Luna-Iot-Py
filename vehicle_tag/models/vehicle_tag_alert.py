from django.db import models
from .vehicle_tag import VehicleTag


class VehicleTagAlert(models.Model):
    """Model for Vehicle Tag Alerts"""
    
    ALERT_TYPE_CHOICES = [
        ('wrong_parking', 'Wrong Parking'),
        ('blocking_road', 'Blocking the road'),
        ('not_locked_ignition_on', 'Not Locked / Ignition ON'),
        ('vehicle_tow_alert', 'Vehicle Tow Alert'),
        ('traffic_rule_violation', 'Traffic Rule Violation'),
        ('fire_physical_threat', 'Fire & Physical Threat'),
        ('accident_alert', 'Accident Alert (Inform Family)'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    vehicle_tag = models.ForeignKey(
        VehicleTag,
        on_delete=models.CASCADE,
        related_name='alerts',
        to_field='vtid',
        db_column='vehicle_tag_vtid',
        help_text="Vehicle tag this alert is for"
    )
    latitude = models.DecimalField(
        max_digits=18,
        decimal_places=15,
        null=True,
        blank=True,
        help_text="Latitude where alert was reported"
    )
    longitude = models.DecimalField(
        max_digits=19,
        decimal_places=15,
        null=True,
        blank=True,
        help_text="Longitude where alert was reported"
    )
    person_image = models.ImageField(
        upload_to='vehicle_tag_alerts/',
        blank=True,
        null=True,
        db_column='person_image',
        help_text="Image of person reporting the alert"
    )
    alert = models.CharField(
        max_length=50,
        choices=ALERT_TYPE_CHOICES,
        db_column='alert',
        help_text="Type of alert"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'vehicle_tag_alerts'
        verbose_name = 'Vehicle Tag Alert'
        verbose_name_plural = 'Vehicle Tag Alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vehicle_tag']),
            models.Index(fields=['alert']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.vehicle_tag.vtid} - {self.get_alert_display()}"

