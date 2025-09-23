from django.db import models


class InstituteService(models.Model):
    """Model for Institute Services"""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    icon = models.CharField(max_length=255, blank=True, null=True, help_text="Icon class or URL for the service")
    description = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'institute_services'
        verbose_name = 'Institute Service'
        verbose_name_plural = 'Institute Services'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name
