"""
User URL Configuration
Matches Node.js user_routes.js endpoints exactly
"""
from django.urls import path
from core.views import user_views

urlpatterns = [
    # List all users
    path('users', user_views.get_all_users, name='get_all_users'),
    
    # Create user (admin) - must come before user/<str:phone> patterns
    path('user/create', user_views.create_user, name='create_user'),
    
    # Update FCM token
    path('fcm-token', user_views.update_fcm_token, name='update_fcm_token'),
    
    # Get user by phone
    path('user/<str:phone>', user_views.get_user_by_phone, name='get_user_by_phone'),
    
    # Update user
    path('user/<str:phone>', user_views.update_user, name='update_user'),
    
    # Delete user
    path('user/<str:phone>', user_views.delete_user, name='delete_user'),
]
