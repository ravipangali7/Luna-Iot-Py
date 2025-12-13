from django.db import models
from core.models import Institute
from shared_utils.constants import AlertSource, AlertStatus


class CommunitySirenHistory(models.Model):
    """Model for Community Siren History"""
    id = models.BigAutoField(primary_key=True)
    source = models.CharField(max_length=20, choices=AlertSource.choices, help_text="Source of the alert (app or switch)")
    name = models.CharField(max_length=255, help_text="Name of the person/entity")
    primary_phone = models.CharField(max_length=20, help_text="Primary contact phone number")
    secondary_phone = models.CharField(max_length=20, blank=True, null=True, help_text="Secondary contact phone number")
    latitude = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=13, decimal_places=8, blank=True, null=True, help_text="Longitude coordinate")
    datetime = models.DateTimeField(help_text="Date and time of the alert")
    images = models.ImageField(upload_to='community_siren_history/', blank=True, null=True, help_text="Alert images")
    remarks = models.TextField(blank=True, null=True, help_text="Additional remarks")
    status = models.CharField(max_length=20, choices=AlertStatus.choices, default=AlertStatus.PENDING, help_text="Status of the alert")
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='community_siren_histories',
        help_text="Institute this alert belongs to"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'community_siren_histories'
        verbose_name = 'Community Siren History'
        verbose_name_plural = 'Community Siren Histories'
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['source']),
            models.Index(fields=['status']),
            models.Index(fields=['institute']),
            models.Index(fields=['datetime']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.source} ({self.datetime.strftime('%Y-%m-%d %H:%M')})"
