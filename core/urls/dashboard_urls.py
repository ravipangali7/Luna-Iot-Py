from django.urls import path
from core.views.dashboard_views import (
    get_dashboard_stats,
    get_user_stats,
    get_device_stats,
    get_vehicle_stats
)

urlpatterns = [
    # Dashboard statistics
    path('stats/', get_dashboard_stats, name='dashboard_stats'),
    path('stats/users/', get_user_stats, name='user_stats'),
    path('stats/devices/', get_device_stats, name='device_stats'),
    path('stats/vehicles/', get_vehicle_stats, name='vehicle_stats'),
]
