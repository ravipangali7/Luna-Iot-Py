"""
Alert Switch URL Patterns
"""
from django.urls import path
from alert_system.views import alert_switch_views

urlpatterns = [
    path('', alert_switch_views.get_all_alert_switches, name='get_all_alert_switches'),
    path('<int:switch_id>/', alert_switch_views.get_alert_switch_by_id, name='get_alert_switch_by_id'),
    path('by-institute/<int:institute_id>/', alert_switch_views.get_alert_switches_by_institute, name='get_alert_switches_by_institute'),
    path('create/', alert_switch_views.create_alert_switch, name='create_alert_switch'),
    path('<int:switch_id>/update/', alert_switch_views.update_alert_switch, name='update_alert_switch'),
    path('<int:switch_id>/delete/', alert_switch_views.delete_alert_switch, name='delete_alert_switch'),
]
