"""
Community Siren Switch URL Patterns
"""
from django.urls import path
from community_siren.views import community_siren_switch_views

urlpatterns = [
    path('', community_siren_switch_views.get_all_community_siren_switches, name='get_all_community_siren_switches'),
    path('<int:switch_id>/', community_siren_switch_views.get_community_siren_switch_by_id, name='get_community_siren_switch_by_id'),
    path('by-institute/<int:institute_id>/', community_siren_switch_views.get_community_siren_switches_by_institute, name='get_community_siren_switches_by_institute'),
    path('create/', community_siren_switch_views.create_community_siren_switch, name='create_community_siren_switch'),
    path('<int:switch_id>/update/', community_siren_switch_views.update_community_siren_switch, name='update_community_siren_switch'),
    path('<int:switch_id>/delete/', community_siren_switch_views.delete_community_siren_switch, name='delete_community_siren_switch'),
]
