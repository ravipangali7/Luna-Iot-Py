"""
Status URL patterns
Matches Node.js status routes exactly
"""
from django.urls import path
from device.views import status_views

urlpatterns = [
    # Status tracking routes
    path('', status_views.create_status, name='create_status'),  # POST endpoint
    path('<str:imei>', status_views.get_status_by_imei, name='get_status_by_imei'),
    path('<str:imei>/latest', status_views.get_latest_status, name='get_latest_status'),
    path('<str:imei>/date-range', status_views.get_status_by_date_range, name='get_status_by_date_range'),
]
