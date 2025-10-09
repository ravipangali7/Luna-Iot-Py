from django.urls import path, include

urlpatterns = [
    path('', include('fleet.urls.vehicle_urls')),
    path('share-track/', include('fleet.urls.share_track_urls')),
]
