from django.db import models
from core.models import Institute
from fleet.models import Vehicle


class SchoolBus(models.Model):
    """Model for School Bus mapping"""
    id = models.BigAutoField(primary_key=True)
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='school_buses',
        help_text="Institute this school bus belongs to"
    )
    bus = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='school_buses',
        help_text="Vehicle assigned as school bus"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'school_buses'
        verbose_name = 'School Bus'
        verbose_name_plural = 'School Buses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['institute']),
            models.Index(fields=['bus']),
            models.Index(fields=['created_at']),
        ]
        unique_together = [['institute', 'bus']]
    
    def __str__(self):
        return f"{self.institute.name} - {self.bus.name} ({self.bus.vehicleNo})"

