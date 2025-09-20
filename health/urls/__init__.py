from django.urls import path, include

urlpatterns = [
    path('', include('health.urls.blood_donation_urls')),
]