"""
Device URL patterns
Matches Node.js device routes exactly
"""
from django.urls import path
from device.views import device_views

urlpatterns = [
    # Device management routes
    path('', device_views.get_all_devices, name='get_all_devices'),
    path('create', device_views.create_device, name='create_device'),
    path('update/<str:imei>', device_views.update_device, name='update_device'),
    path('delete/<str:imei>', device_views.delete_device, name='delete_device'),
    path('assign', device_views.assign_device_to_user, name='assign_device_to_user'),
    path('remove-assignment', device_views.remove_device_assignment, name='remove_device_assignment'),
    path('server-point', device_views.send_server_point, name='send_server_point'),
    path('reset', device_views.send_reset, name='send_reset'),
    path('<str:imei>', device_views.get_device_by_imei, name='get_device_by_imei'),
]
