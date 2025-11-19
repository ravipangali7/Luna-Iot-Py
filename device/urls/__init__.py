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
    
    # Subscription plan routes
    path('subscription-plan/', include('device.urls.subscription_plan_urls')),
    
    # Device order routes
    path('', include('device.urls.device_order_urls')),
    
    # Luna Tag routes
    path('luna-tag/', include('device.urls.luna_tag_urls')),
    
    # User Luna Tag routes
    path('user-luna-tag/', include('device.urls.user_luna_tag_urls')),
    
    # Luna Tag Data routes
    path('luna-tag-data/', include('device.urls.luna_tag_data_urls')),
    
    # Alert device routes
    path('', include('device.urls.alert_device_urls')),
]
