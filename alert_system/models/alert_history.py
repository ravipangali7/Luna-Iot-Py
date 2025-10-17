from django.db import models
from core.models import Institute
from shared_utils.constants import AlertSource, AlertStatus


class AlertHistory(models.Model):
    """Model for Alert History"""
    id = models.BigAutoField(primary_key=True)
    source = models.CharField(max_length=20, choices=AlertSource.choices, help_text="Source of the alert")
    name = models.CharField(max_length=255, help_text="Name of the person/entity")
    primary_phone = models.CharField(max_length=20, help_text="Primary contact phone number")
    secondary_phone = models.CharField(max_length=20, blank=True, null=True, help_text="Secondary contact phone number")
    alert_type = models.ForeignKey(
        'AlertType',
        on_delete=models.CASCADE,
        related_name='alert_histories',
        help_text="Type of alert"
    )
    latitude = models.DecimalField(max_digits=10, decimal_places=8, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=11, decimal_places=8, help_text="Longitude coordinate")
    datetime = models.DateTimeField(help_text="Date and time of the alert")
    image = models.ImageField(upload_to='alert_history/', blank=True, null=True, help_text="Alert image")
    remarks = models.TextField(blank=True, null=True, help_text="Additional remarks")
    status = models.CharField(max_length=20, choices=AlertStatus.choices, default=AlertStatus.PENDING, help_text="Status of the alert")
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='alert_histories',
        help_text="Institute this alert belongs to"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'alert_histories'
        verbose_name = 'Alert History'
        verbose_name_plural = 'Alert Histories'
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['source']),
            models.Index(fields=['status']),
            models.Index(fields=['institute']),
            models.Index(fields=['datetime']),
            models.Index(fields=['alert_type']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.alert_type.name} ({self.datetime.strftime('%Y-%m-%d %H:%M')})"
