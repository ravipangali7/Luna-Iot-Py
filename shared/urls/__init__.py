from django.urls import path, include

urlpatterns = [
    path('shared/', include('shared.urls.geofence_urls')),
    path('shared/', include('shared.urls.notification_urls')),
    path('shared/', include('shared.urls.popup_urls')),
    path('shared/', include('shared.urls.recharge_urls')),
]
