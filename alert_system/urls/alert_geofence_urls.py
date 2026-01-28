"""
Alert Geofence URL Patterns
"""
from django.urls import path
from alert_system.views import alert_geofence_views

urlpatterns = [
    path('', alert_geofence_views.get_all_alert_geofences, name='get_all_alert_geofences'),
    path('sos/', alert_geofence_views.get_sos_alert_geofences, name='get_sos_alert_geofences'),
    path('import-boundary/', alert_geofence_views.import_boundary, name='import_boundary'),
    path('<int:geofence_id>/', alert_geofence_views.get_alert_geofence_by_id, name='get_alert_geofence_by_id'),
    path('by-institute/<int:institute_id>/', alert_geofence_views.get_alert_geofences_by_institute, name='get_alert_geofences_by_institute'),
    path('create/', alert_geofence_views.create_alert_geofence, name='create_alert_geofence'),
    path('<int:geofence_id>/update/', alert_geofence_views.update_alert_geofence, name='update_alert_geofence'),
    path('<int:geofence_id>/delete/', alert_geofence_views.delete_alert_geofence, name='delete_alert_geofence'),
]
