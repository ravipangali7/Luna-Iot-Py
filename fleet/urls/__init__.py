from django.urls import path, include

urlpatterns = [
    path('', include('fleet.urls.vehicle_urls')),
]
