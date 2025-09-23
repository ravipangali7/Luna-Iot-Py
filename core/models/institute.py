from django.db import models
from .institute_service import InstituteService


class Institute(models.Model):
    """Model for Institutes"""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True, help_text="Longitude coordinate")
    logo = models.ImageField(upload_to='institutes/logos/', blank=True, null=True, help_text="Institute logo image")
    institute_services = models.ManyToManyField(
        InstituteService, 
        blank=True, 
        related_name='institutes',
        help_text="Services offered by this institute"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'institutes'
        verbose_name = 'Institute'
        verbose_name_plural = 'Institutes'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['phone']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def location(self):
        """Return formatted location string"""
        if self.latitude and self.longitude:
            return f"{self.latitude}, {self.longitude}"
        return None
