"""
URL configuration for luna_iot_py project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include

urlpatterns = [
    # Core module URLs
    path('api/core/', include('core.urls')),
    
    # Shared module URLs
    path('api/shared/', include('shared.urls')),
    # Public short links (root-level)
    path('', include('shared.urls.short_link_urls')),
    
    # Device module URLs
    path('api/device/', include('device.urls')),
    
    # Fleet module URLs
    path('api/fleet/', include('fleet.urls')),
    
    # Health module URLs
    path('api/health/', include('health.urls')),
    
    # Finance module URLs
    path('api/finance/', include('finance.urls')),
    
    # Alert System module URLs
    path('api/alert-system/', include('alert_system.urls')),
    
    # Admin URLs
    path('admin/', admin.site.urls),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)