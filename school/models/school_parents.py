from django.db import models
from core.models import User


class SchoolParent(models.Model):
    """Model for School Parents"""
    id = models.BigAutoField(primary_key=True)
    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='school_parents',
        help_text="Parent user"
    )
    school_buses = models.ManyToManyField(
        'SchoolBus',
        blank=True,
        related_name='school_parents',
        help_text="School buses this parent is associated with"
    )
    latitude = models.DecimalField(
        max_digits=12,
        decimal_places=8,
        blank=True,
        null=True,
        help_text="Parent location latitude"
    )
    longitude = models.DecimalField(
        max_digits=13,
        decimal_places=8,
        blank=True,
        null=True,
        help_text="Parent location longitude"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'school_parents'
        verbose_name = 'School Parent'
        verbose_name_plural = 'School Parents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.parent.name or self.parent.phone}"

