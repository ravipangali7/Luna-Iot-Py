"""
Alert History URL Patterns
"""
from django.urls import path
from alert_system.views import alert_history_views

urlpatterns = [
    path('', alert_history_views.get_all_alert_histories, name='get_all_alert_histories'),
    path('<int:history_id>/', alert_history_views.get_alert_history_by_id, name='get_alert_history_by_id'),
    path('by-institute/<int:institute_id>/', alert_history_views.get_alert_histories_by_institute, name='get_alert_histories_by_institute'),
    path('by-radar/<int:radar_id>/', alert_history_views.get_alert_histories_by_radar, name='get_alert_histories_by_radar'),
    path('statistics/', alert_history_views.get_alert_history_statistics, name='get_alert_history_statistics'),
    path('create/', alert_history_views.create_alert_history, name='create_alert_history'),
    path('<int:history_id>/update/', alert_history_views.update_alert_history, name='update_alert_history'),
    path('<int:history_id>/update-status/', alert_history_views.update_alert_history_status, name='update_alert_history_status'),
    path('<int:history_id>/update-remarks/', alert_history_views.update_alert_history_remarks, name='update_alert_history_remarks'),  # NEW
    path('<int:history_id>/delete/', alert_history_views.delete_alert_history, name='delete_alert_history'),
]
