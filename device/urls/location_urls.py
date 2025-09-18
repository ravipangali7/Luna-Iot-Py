"""
Location URL patterns
Matches Node.js location routes exactly
"""
from django.urls import path
from device.views import location_views

urlpatterns = [
    # Location tracking routes
    path('', location_views.create_location, name='create_location'),  # POST endpoint
    path('<str:imei>', location_views.get_location_by_imei, name='get_location_by_imei'),
    path('<str:imei>/latest', location_views.get_latest_location, name='get_latest_location'),
    path('<str:imei>/date-range', location_views.get_location_by_date_range, name='get_location_by_date_range'),
    path('<str:imei>/combined-history', location_views.get_combined_history_by_date_range, name='get_combined_history_by_date_range'),
    path('<str:imei>/report', location_views.generate_report, name='generate_report'),
]
