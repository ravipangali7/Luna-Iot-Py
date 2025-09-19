"""
User Permission URL Configuration
Matches Node.js user_permission_routes.js endpoints exactly
"""
from django.urls import path
from core.views import user_permission_views

urlpatterns = [
    # Get all permissions for a user - match Flutter expectation
    path('user/<int:userId>/permissions', user_permission_views.get_user_permissions, name='get_user_permissions'),
    
    # Get combined permissions (role + direct) for a user
    path('user/<int:userId>/combined-permissions', user_permission_views.get_combined_user_permissions, name='get_combined_user_permissions'),
    
    # Assign permission to user
    path('assign-permission', user_permission_views.assign_permission_to_user, name='assign_permission_to_user'),
    
    # Remove permission from user
    path('remove-permission', user_permission_views.remove_permission_from_user, name='remove_permission_from_user'),
    
    # Assign multiple permissions to user
    path('assign-multiple-permissions', user_permission_views.assign_multiple_permissions_to_user, name='assign_multiple_permissions_to_user'),
    
    # Remove all permissions from user
    path('user/<int:userId>/permissions', user_permission_views.remove_all_permissions_from_user, name='remove_all_permissions_from_user'),
    
    # Check if user has specific permission
    path('user/<int:userId>/has-permission/<str:permissionName>', user_permission_views.check_user_permission, name='check_user_permission'),
    
    # Get all available permissions
    path('permissions', user_permission_views.get_all_permissions, name='get_all_permissions'),
    
    # Get users with specific permission
    path('permission/<int:permissionId>/users', user_permission_views.get_users_with_permission, name='get_users_with_permission'),
]
