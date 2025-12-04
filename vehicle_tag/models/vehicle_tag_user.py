from django.db import models
from core.models import User
from .vehicle_tag import VehicleTag


class VehicleTagUser(models.Model):
    """Model for Vehicle Tag User Assignment"""
    
    id = models.BigAutoField(primary_key=True)
    vehicle_tag = models.ForeignKey(
        VehicleTag,
        on_delete=models.CASCADE,
        related_name='tag_users',
        db_column='vehicle_tag_id',
        help_text="Vehicle tag being assigned"
    )
    vtid = models.CharField(
        max_length=50,
        db_column='vtid',
        help_text="Vehicle Tag ID for quick reference"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vehicle_tag_assignments',
        help_text="User assigned to this vehicle tag"
    )
    is_active = models.BooleanField(
        default=True,
        db_column='is_active',
        help_text="Whether this assignment is active"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'vehicle_tag_users'
        verbose_name = 'Vehicle Tag User'
        verbose_name_plural = 'Vehicle Tag Users'
        unique_together = [['vehicle_tag', 'user']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vehicle_tag']),
            models.Index(fields=['user']),
            models.Index(fields=['vtid']),
            models.Index(fields=['is_active']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-populate vtid from vehicle_tag
        if self.vehicle_tag:
            self.vtid = self.vehicle_tag.vtid
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.vtid} - {self.user.name or self.user.phone}"

