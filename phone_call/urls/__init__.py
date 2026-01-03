# Phone Call URLs Package
from django.urls import path, include

urlpatterns = [
    path('', include('phone_call.urls.campaign_urls')),
    path('', include('phone_call.urls.phone_book_urls')),
]

