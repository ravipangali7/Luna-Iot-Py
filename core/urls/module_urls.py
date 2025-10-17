"""
Module URL Patterns
Handles all module-related API endpoints
"""
from django.urls import path
from core.views import module_views

urlpatterns = [
    # Module URLs
    path('', module_views.get_all_modules, name='get_all_modules'),
    path('<int:module_id>/', module_views.get_module_by_id, name='get_module_by_id'),
    path('create/', module_views.create_module, name='create_module'),
    path('<int:module_id>/update/', module_views.update_module, name='update_module'),
    path('<int:module_id>/delete/', module_views.delete_module, name='delete_module'),
]
