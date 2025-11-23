from django.urls import path, include

urlpatterns = [
    # Garbage Vehicle routes
    path('garbage-vehicle/', include('garbage.urls.garbage_vehicle_urls')),
]

