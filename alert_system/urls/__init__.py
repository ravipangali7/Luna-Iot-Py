from django.urls import path, include

urlpatterns = [
    # Alert Type routes
    path('alert-type/', include('alert_system.urls.alert_type_urls')),
    
    # Alert Geofence routes
    path('alert-geofence/', include('alert_system.urls.alert_geofence_urls')),
    
    # Alert Radar routes
    path('alert-radar/', include('alert_system.urls.alert_radar_urls')),
    
    # Alert Buzzer routes
    path('alert-buzzer/', include('alert_system.urls.alert_buzzer_urls')),
    
    # Alert Contact routes
    path('alert-contact/', include('alert_system.urls.alert_contact_urls')),
    
    # Alert Switch routes
    path('alert-switch/', include('alert_system.urls.alert_switch_urls')),
    
    # Alert History routes
    path('alert-history/', include('alert_system.urls.alert_history_urls')),
]
