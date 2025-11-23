"""
Institute URL Patterns
Handles all institute-related API endpoints
"""
from django.urls import path
from core.views import (
    institute_service_views,
    institute_views,
    institute_module_views
)

urlpatterns = [
    # Institute Service URLs
    path('services/', institute_service_views.get_all_institute_services, name='get_all_institute_services'),
    path('services/<int:service_id>/', institute_service_views.get_institute_service_by_id, name='get_institute_service_by_id'),
    path('services/create/', institute_service_views.create_institute_service, name='create_institute_service'),
    path('services/<int:service_id>/update/', institute_service_views.update_institute_service, name='update_institute_service'),
    path('services/<int:service_id>/delete/', institute_service_views.delete_institute_service, name='delete_institute_service'),
    
    # Institute URLs
    path('', institute_views.get_all_institutes, name='get_all_institutes'),
    path('paginated/', institute_views.get_institutes_paginated, name='get_institutes_paginated'),
    path('<int:institute_id>/', institute_views.get_institute_by_id, name='get_institute_by_id'),
    path('create/', institute_views.create_institute, name='create_institute'),
    path('<int:institute_id>/update/', institute_views.update_institute, name='update_institute'),
    path('<int:institute_id>/delete/', institute_views.delete_institute, name='delete_institute'),
    path('locations/', institute_views.get_institute_locations, name='get_institute_locations'),
    
    # Institute Module URLs
    path('modules/', institute_module_views.get_all_institute_modules, name='get_all_institute_modules'),
    path('modules/<int:module_id>/', institute_module_views.get_institute_module_by_id, name='get_institute_module_by_id'),
    path('modules/create/', institute_module_views.create_institute_module, name='create_institute_module'),
    path('modules/<int:module_id>/update/', institute_module_views.update_institute_module, name='update_institute_module'),
    path('modules/<int:module_id>/delete/', institute_module_views.delete_institute_module, name='delete_institute_module'),
    path('modules/<int:module_id>/users/', institute_module_views.update_institute_module_users, name='update_institute_module_users'),
    path('modules/alert-system-institutes/', institute_module_views.get_alert_system_institutes, name='get_alert_system_institutes'),
    path('modules/school-institutes/', institute_module_views.get_school_institutes, name='get_school_institutes'),
    path('modules/garbage-institutes/', institute_module_views.get_garbage_institutes, name='get_garbage_institutes'),
    path('<int:institute_id>/modules/', institute_module_views.get_institute_modules_by_institute, name='get_institute_modules_by_institute'),
]
