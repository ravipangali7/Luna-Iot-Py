"""
Alert Contact URL Patterns
"""
from django.urls import path
from alert_system.views import alert_contact_views

urlpatterns = [
    path('', alert_contact_views.get_all_alert_contacts, name='get_all_alert_contacts'),
    path('<int:contact_id>/', alert_contact_views.get_alert_contact_by_id, name='get_alert_contact_by_id'),
    path('by-institute/<int:institute_id>/', alert_contact_views.get_alert_contacts_by_institute, name='get_alert_contacts_by_institute'),
    path('create/', alert_contact_views.create_alert_contact, name='create_alert_contact'),
    path('<int:contact_id>/update/', alert_contact_views.update_alert_contact, name='update_alert_contact'),
    path('<int:contact_id>/delete/', alert_contact_views.delete_alert_contact, name='delete_alert_contact'),
]
