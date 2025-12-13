from django.db import models
from core.models import Institute
from device.models import Device


class CommunitySirenBuzzer(models.Model):
    """Model for Community Siren Buzzers"""
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='community_siren_buzzers',
        help_text="Device associated with this buzzer"
    )
    delay = models.IntegerField(help_text="Delay in seconds before buzzer activation")
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='community_siren_buzzers',
        help_text="Institute this buzzer belongs to"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'community_siren_buzzers'
        verbose_name = 'Community Siren Buzzer'
        verbose_name_plural = 'Community Siren Buzzers'
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['institute']),
            models.Index(fields=['device']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.device.imei})"
