from django.db import models


class AlertType(models.Model):
    """Model for Alert Types"""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    icon = models.CharField(max_length=255, blank=True, null=True, help_text="Icon class or URL for the alert type")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'alert_types'
        verbose_name = 'Alert Type'
        verbose_name_plural = 'Alert Types'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name