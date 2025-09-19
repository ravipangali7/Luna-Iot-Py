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
    path('permissions', role_views.permission_handler, name='permission_handler'),
    path('permissions/<int:id>', role_views.permission_by_id_handler, name='permission_by_id_handler'),
]
