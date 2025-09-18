from django.urls import path, include

urlpatterns = [
    path('', include('shared.urls.geofence_urls')),
    path('', include('shared.urls.notification_urls')),
    path('', include('shared.urls.popup_urls')),
    path('', include('shared.urls.recharge_urls')),
]
