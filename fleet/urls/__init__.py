from django.urls import path, include

urlpatterns = [
    path('share-track/', include('fleet.urls.share_track_urls')),
    path('', include('fleet.urls.vehicle_urls')),
    path('', include('fleet.urls.fleet_management_urls')),
]
