from django.urls import path, include

urlpatterns = [
    # Authentication routes
    path('auth/', include('core.urls.auth_urls')),
    
    # User routes
    path('user/', include('core.urls.user_urls')),
    
    # Role routes
    path('', include('core.urls.role_urls')),
    
    # User permission routes (at root level to match Flutter expectations)
    path('', include('core.urls.user_permission_urls')),
    
    # Permission routes (for /api/core/permission/...)
    path('permission/', include('core.urls.role_urls')),
]
