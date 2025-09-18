from django.urls import path, include

urlpatterns = [
    # Device management routes
    path('device/', include('device.urls.device_urls')),
    
    # Location tracking routes
    path('location/', include('device.urls.location_urls')),
    
    # Status tracking routes
    path('status/', include('device.urls.status_urls')),
    
    # Relay control routes
    path('relay/', include('device.urls.relay_urls')),
]
