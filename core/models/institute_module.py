from django.db import models
from .institute import Institute
from .user import User
from .module import Module


class InstituteModule(models.Model):
    """Model for Institute Modules - linking institutes with modules and users"""
    id = models.BigAutoField(primary_key=True)
    institute = models.ForeignKey(
        Institute, 
        on_delete=models.CASCADE, 
        related_name='modules',
        help_text="The institute this module belongs to"
    )
    module = models.ForeignKey(
        Module, 
        on_delete=models.CASCADE, 
        related_name='institute_modules',
        null=True,
        help_text="Module for this institute module"
    )
    users = models.ManyToManyField(
        User, 
        blank=True, 
        related_name='institute_modules',
        help_text="Users assigned to this institute module"
    )
    
    expire_date = models.DateTimeField(
        null=True, 
        blank=True, 
        db_column='expire_date',
        help_text="Expiration date for this institute module"
    )
    renewal_price = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        db_column='renewal_price',
        help_text="Renewal price for this institute module"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'institute_modules'
        verbose_name = 'Institute Module'
        verbose_name_plural = 'Institute Modules'
        ordering = ['institute__name', 'module__name']
        unique_together = ['institute', 'module']  # Each institute can have only one module per module
        indexes = [
            models.Index(fields=['institute']),
            models.Index(fields=['module']),
        ]
    
    def __str__(self):
        return f"{self.institute.name} - {self.module.name}"
    
    @property
    def user_count(self):
        """Return the number of users in this module"""
        return self.users.count()
