"""
Alert Radar URL Patterns
"""
from django.urls import path
from alert_system.views import alert_radar_views

urlpatterns = [
    path('', alert_radar_views.get_all_alert_radars, name='get_all_alert_radars'),
    path('<int:radar_id>/', alert_radar_views.get_alert_radar_by_id, name='get_alert_radar_by_id'),
    path('by-institute/<int:institute_id>/', alert_radar_views.get_alert_radars_by_institute, name='get_alert_radars_by_institute'),
    path('token/<str:token>/', alert_radar_views.get_alert_radar_by_token, name='get_alert_radar_by_token'),
    path('create/', alert_radar_views.create_alert_radar, name='create_alert_radar'),
    path('<int:radar_id>/update/', alert_radar_views.update_alert_radar, name='update_alert_radar'),
    path('<int:radar_id>/delete/', alert_radar_views.delete_alert_radar, name='delete_alert_radar'),
]