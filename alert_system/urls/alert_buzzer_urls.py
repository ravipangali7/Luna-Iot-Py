"""
Alert Buzzer URL Patterns
"""
from django.urls import path
from alert_system.views import alert_buzzer_views

urlpatterns = [
    path('', alert_buzzer_views.get_all_alert_buzzers, name='get_all_alert_buzzers'),
    path('<int:buzzer_id>/', alert_buzzer_views.get_alert_buzzer_by_id, name='get_alert_buzzer_by_id'),
    path('by-institute/<int:institute_id>/', alert_buzzer_views.get_alert_buzzers_by_institute, name='get_alert_buzzers_by_institute'),
    path('create/', alert_buzzer_views.create_alert_buzzer, name='create_alert_buzzer'),
    path('<int:buzzer_id>/update/', alert_buzzer_views.update_alert_buzzer, name='update_alert_buzzer'),
    path('<int:buzzer_id>/delete/', alert_buzzer_views.delete_alert_buzzer, name='delete_alert_buzzer'),
]
