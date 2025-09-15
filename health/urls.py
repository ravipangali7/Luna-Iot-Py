from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
# Add viewsets here when we create them

urlpatterns = [
    path('', include(router.urls)),
]