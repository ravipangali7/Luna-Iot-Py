"""
Community Siren Buzzer URL Patterns
"""
from django.urls import path
from community_siren.views import community_siren_buzzer_views

urlpatterns = [
    path('', community_siren_buzzer_views.get_all_community_siren_buzzers, name='get_all_community_siren_buzzers'),
    path('<int:buzzer_id>/', community_siren_buzzer_views.get_community_siren_buzzer_by_id, name='get_community_siren_buzzer_by_id'),
    path('by-institute/<int:institute_id>/', community_siren_buzzer_views.get_community_siren_buzzers_by_institute, name='get_community_siren_buzzers_by_institute'),
    path('create/', community_siren_buzzer_views.create_community_siren_buzzer, name='create_community_siren_buzzer'),
    path('<int:buzzer_id>/update/', community_siren_buzzer_views.update_community_siren_buzzer, name='update_community_siren_buzzer'),
    path('<int:buzzer_id>/delete/', community_siren_buzzer_views.delete_community_siren_buzzer, name='delete_community_siren_buzzer'),
]
