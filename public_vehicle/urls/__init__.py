from django.urls import path, include

urlpatterns = [
    # Public Vehicle routes
    path('public-vehicle/', include('public_vehicle.urls.public_vehicle_urls')),
]

