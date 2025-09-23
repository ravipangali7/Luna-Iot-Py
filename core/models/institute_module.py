from django.db import models
from django.contrib.auth.models import Group
from .institute import Institute
from .user import User


class InstituteModule(models.Model):
    """Model for Institute Modules - linking institutes with groups and users"""
    id = models.BigAutoField(primary_key=True)
    institute = models.ForeignKey(
        Institute, 
        on_delete=models.CASCADE, 
        related_name='modules',
        help_text="The institute this module belongs to"
    )
    group = models.ForeignKey(
        Group, 
        on_delete=models.CASCADE, 
        related_name='institute_modules',
        help_text="Django auth group for this module"
    )
    users = models.ManyToManyField(
        User, 
        blank=True, 
        related_name='institute_modules',
        help_text="Users assigned to this institute module"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'institute_modules'
        verbose_name = 'Institute Module'
        verbose_name_plural = 'Institute Modules'
        ordering = ['institute__name', 'group__name']
        unique_together = ['institute', 'group']  # Each institute can have only one module per group
        indexes = [
            models.Index(fields=['institute']),
            models.Index(fields=['group']),
        ]
    
    def __str__(self):
        return f"{self.institute.name} - {self.group.name}"
    
    @property
    def user_count(self):
        """Return the number of users in this module"""
        return self.users.count()
