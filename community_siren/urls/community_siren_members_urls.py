"""
Community Siren Members URL Patterns
"""
from django.urls import path
from community_siren.views import community_siren_members_views

urlpatterns = [
    path('', community_siren_members_views.get_all_community_siren_members, name='get_all_community_siren_members'),
    path('access/', community_siren_members_views.check_member_access, name='check_member_access'),
    path('by-institute/<int:institute_id>/', community_siren_members_views.get_community_siren_members_by_institute, name='get_community_siren_members_by_institute'),
    path('<int:member_id>/', community_siren_members_views.get_community_siren_member_by_id, name='get_community_siren_member_by_id'),
    path('create/', community_siren_members_views.create_community_siren_member, name='create_community_siren_member'),
    path('<int:member_id>/update/', community_siren_members_views.update_community_siren_member, name='update_community_siren_member'),
    path('<int:member_id>/delete/', community_siren_members_views.delete_community_siren_member, name='delete_community_siren_member'),
]
