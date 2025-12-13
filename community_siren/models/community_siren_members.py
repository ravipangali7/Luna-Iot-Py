from django.db import models
from core.models import User


class CommunitySirenMembers(models.Model):
    """Model for Community Siren Members"""
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='community_siren_members',
        help_text="User who is a member of community siren"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'community_siren_members'
        verbose_name = 'Community Siren Member'
        verbose_name_plural = 'Community Siren Members'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
        ]
        unique_together = ['user']  # Each user can only be a member once
    
    def __str__(self):
        return f"{self.user.name or self.user.phone}"
