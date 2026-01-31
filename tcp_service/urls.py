"""
TCP Service URL Configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    path('dashcam/command/', views.dashcam_command, name='dashcam-command'),
    path('dashcam/devices/', views.dashcam_devices, name='dashcam-devices'),
    path('dashcam/status/<str:imei>/', views.dashcam_connection_status, name='dashcam-status'),
]
