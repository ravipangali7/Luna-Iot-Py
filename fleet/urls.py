from django.urls import path, include

urlpatterns = [
    path('fleet/', include('fleet.urls.vehicle_urls')),
]