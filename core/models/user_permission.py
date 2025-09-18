from django.db import models
from django.contrib.auth.models import Permission
from .user import User


class UserPermission(models.Model):
    """User-Permission relationship model"""
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userpermission_set')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='userpermissions')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    
    class Meta:
        unique_together = ['user', 'permission']
        db_table = 'user_permissions'
        indexes = [
            models.Index(fields=['user', 'permission']),
        ]
    
    def __str__(self):
        return f"{self.user.name} - {self.permission.name}"