from django.db import models
from core.models import Institute


class AlertContact(models.Model):
    """Model for Alert Contacts"""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    alert_geofences = models.ManyToManyField(
        'AlertGeofence',
        blank=True,
        related_name='alert_contacts',
        help_text="Geofences this contact is associated with"
    )
    alert_types = models.ManyToManyField(
        'AlertType',
        blank=True,
        related_name='alert_contacts',
        help_text="Alert types this contact should be notified about"
    )
    is_sms = models.BooleanField(default=True, help_text="Send SMS notifications")
    is_call = models.BooleanField(default=False, help_text="Make phone calls")
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='alert_contacts',
        help_text="Institute this contact belongs to"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'alert_contacts'
        verbose_name = 'Alert Contact'
        verbose_name_plural = 'Alert Contacts'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['phone']),
            models.Index(fields=['institute']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.phone})"