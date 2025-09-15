"""
Role URL Configuration
Matches Node.js role_routes.js endpoints exactly
"""
from django.urls import path
from core.views import role_views

urlpatterns = [
    # Get all roles
    path('roles', role_views.get_all_roles, name='get_all_roles'),
    
    # Get role by ID
    path('roles/<int:id>', role_views.get_role_by_id, name='get_role_by_id'),
    
    # Update role permissions (edit only permissions)
    path('roles/<int:id>/permissions', role_views.update_role_permissions, name='update_role_permissions'),
    
    # Permission Management Routes
    path('permissions', role_views.get_all_permissions, name='get_all_permissions'),
    path('permissions/<int:id>', role_views.get_permission_by_id, name='get_permission_by_id'),
    path('permissions', role_views.create_permission, name='create_permission'),
    path('permissions/<int:id>', role_views.update_permission, name='update_permission'),
    path('permissions/<int:id>', role_views.delete_permission, name='delete_permission'),
]
