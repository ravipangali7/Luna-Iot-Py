from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model with phone as primary identifier"""
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)  # Will store phone number
    phone = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    fcm_token = models.CharField(max_length=500, null=True, blank=True, db_column='fcm_token')
    token = models.CharField(max_length=500, null=True, blank=True)
    
    first_name = None
    last_name = None
    
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username']
    
    # Timestamps matching Prisma
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['phone', 'username', 'fcm_token']),
        ]

    def save(self, *args, **kwargs):
        # Automatically set username to phone value
        self.username = self.phone
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name or self.username} ({self.phone})"

    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    @property
    def role(self):
        """
        Get the primary role (first group) for backward compatibility
        """
        primary_group = self.groups.first()
        if primary_group:
            return type('Role', (), {'name': primary_group.name})()
        return None