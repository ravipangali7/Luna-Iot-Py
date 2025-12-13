"""
Community Siren Contact URL Patterns
"""
from django.urls import path
from community_siren.views import community_siren_contact_views

urlpatterns = [
    path('', community_siren_contact_views.get_all_community_siren_contacts, name='get_all_community_siren_contacts'),
    path('<int:contact_id>/', community_siren_contact_views.get_community_siren_contact_by_id, name='get_community_siren_contact_by_id'),
    path('by-institute/<int:institute_id>/', community_siren_contact_views.get_community_siren_contacts_by_institute, name='get_community_siren_contacts_by_institute'),
    path('create/', community_siren_contact_views.create_community_siren_contact, name='create_community_siren_contact'),
    path('<int:contact_id>/update/', community_siren_contact_views.update_community_siren_contact, name='update_community_siren_contact'),
    path('<int:contact_id>/delete/', community_siren_contact_views.delete_community_siren_contact, name='delete_community_siren_contact'),
]
