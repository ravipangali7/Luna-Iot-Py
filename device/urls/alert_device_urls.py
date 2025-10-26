"""
Alert Device URLs
"""
from django.urls import path
from device.views import alert_device_views

urlpatterns = [
    path('alert-devices', alert_device_views.get_alert_devices, name='get-alert-devices'),
]

