from django.db import models
from core.models import Institute


class SchoolSMS(models.Model):
    """Model for School SMS messages"""
    id = models.BigAutoField(primary_key=True)
    message = models.TextField(help_text="SMS message content")
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='school_sms',
        help_text="Institute this SMS belongs to"
    )
    phone_numbers = models.JSONField(
        default=list,
        help_text="List of phone numbers to send SMS to"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'school_sms'
        verbose_name = 'School SMS'
        verbose_name_plural = 'School SMS'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['institute']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"SMS for {self.institute.name} ({len(self.phone_numbers) if self.phone_numbers else 0} recipients)"

