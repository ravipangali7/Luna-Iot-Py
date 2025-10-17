"""
Alert Type URL Patterns
"""
from django.urls import path
from alert_system.views import alert_type_views

urlpatterns = [
    path('', alert_type_views.get_all_alert_types, name='get_all_alert_types'),
    path('<int:alert_type_id>/', alert_type_views.get_alert_type_by_id, name='get_alert_type_by_id'),
    path('create/', alert_type_views.create_alert_type, name='create_alert_type'),
    path('<int:alert_type_id>/update/', alert_type_views.update_alert_type, name='update_alert_type'),
    path('<int:alert_type_id>/delete/', alert_type_views.delete_alert_type, name='delete_alert_type'),
]
