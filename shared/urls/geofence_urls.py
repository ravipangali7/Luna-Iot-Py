from django.urls import path
from shared.views import geofence_views

urlpatterns = [
    path('geofence', geofence_views.create_geofence, name='create_geofence'),
    path('geofence/all', geofence_views.get_all_geofences, name='get_all_geofences'),
    path('geofence/<int:id>', geofence_views.get_geofence_by_id, name='get_geofence_by_id'),
    path('geofence/imei/<str:imei>', geofence_views.get_geofences_by_imei, name='get_geofences_by_imei'),
    path('geofence/update/<int:id>', geofence_views.update_geofence, name='update_geofence'),
    path('geofence/delete/<int:id>', geofence_views.delete_geofence, name='delete_geofence'),
]
