"""
Community Siren History URL Patterns
"""
from django.urls import path
from community_siren.views import community_siren_history_views

urlpatterns = [
    path('', community_siren_history_views.get_all_community_siren_histories, name='get_all_community_siren_histories'),
    path('<int:history_id>/', community_siren_history_views.get_community_siren_history_by_id, name='get_community_siren_history_by_id'),
    path('by-institute/<int:institute_id>/', community_siren_history_views.get_community_siren_histories_by_institute, name='get_community_siren_histories_by_institute'),
    path('create/', community_siren_history_views.create_community_siren_history, name='create_community_siren_history'),
    path('<int:history_id>/update/', community_siren_history_views.update_community_siren_history, name='update_community_siren_history'),
    path('<int:history_id>/update-status/', community_siren_history_views.update_community_siren_history_status, name='update_community_siren_history_status'),
    path('<int:history_id>/delete/', community_siren_history_views.delete_community_siren_history, name='delete_community_siren_history'),
]
