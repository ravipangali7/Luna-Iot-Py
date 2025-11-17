"""
Settings URL Configuration
"""
from django.urls import path
from core.views import settings_views

urlpatterns = [
    # Settings endpoint - handles both GET and PUT
    path('', settings_views.settings_handler, name='settings_handler'),
]

