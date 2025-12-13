from django.db import models
from core.models import Institute


class CommunitySirenContact(models.Model):
    """Model for Community Siren Contacts"""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    is_sms = models.BooleanField(default=True, help_text="Send SMS notifications")
    is_call = models.BooleanField(default=False, help_text="Make phone calls")
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='community_siren_contacts',
        help_text="Institute this contact belongs to"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'community_siren_contacts'
        verbose_name = 'Community Siren Contact'
        verbose_name_plural = 'Community Siren Contacts'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['phone']),
            models.Index(fields=['institute']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.phone})"
