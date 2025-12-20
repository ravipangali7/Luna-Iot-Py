from django.urls import path, include

urlpatterns = [
    path('', include('shared.urls.geofence_urls')),
    path('', include('shared.urls.notification_urls')),
    path('', include('shared.urls.popup_urls')),
    path('', include('shared.urls.recharge_urls')),
    path('', include('shared.urls.short_link_urls')),
    path('', include('shared.urls.short_link_api_urls')),
    path('', include('shared.urls.external_app_link_urls')),
    path('', include('shared.urls.banner_urls')),
    path('', include('shared.urls.ntc_m2m_urls')),
]
