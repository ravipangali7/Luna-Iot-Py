"""
User URL Configuration
Matches Node.js user_routes.js endpoints exactly
"""
from django.urls import path
from core.views import user_views

urlpatterns = [
    # List all users
    path('users', user_views.get_all_users, name='get_all_users'),
    
    # List users with pagination and search
    path('users/paginated', user_views.get_users_paginated, name='get_users_paginated'),
    
    # Create user (admin) - must come before user/<str:phone> patterns
    path('user/create', user_views.create_user, name='create_user'),
    
    # Update FCM token
    path('fcm-token', user_views.update_fcm_token, name='update_fcm_token'),
    
    # User operations by phone - Django will route based on HTTP method
    path('user/<str:phone>', user_views.user_by_phone_handler, name='user_by_phone_handler'),
]
