from django.db import models
from django.contrib.auth.models import Group, Permission

class Role(models.Model):
    """Custom Role model that extends Django's Group"""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updatedAt = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    # Link to Django's Group for permissions
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='custom_role')
    
    class Meta:
        db_table = 'roles'
    
    def __str__(self):
        return self.name

class RolePermission(models.Model):
    """Custom Role-Permission relationship"""
    id = models.BigAutoField(primary_key=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='roles')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    
    class Meta:
        unique_together = ['role', 'permission']
        db_table = 'role_permissions'
    
    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"
