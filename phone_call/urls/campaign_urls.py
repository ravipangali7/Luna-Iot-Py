"""
Phone Call Campaign URLs
URL patterns for campaign management endpoints
"""
from django.urls import path
from phone_call.views import campaign_views

urlpatterns = [
    # Voice Models
    path('voice-models/', campaign_views.get_voice_models, name='get_voice_models'),
    
    # Phone Numbers
    path('phone-numbers/active/', campaign_views.get_active_phone_numbers, name='get_active_phone_numbers'),
    
    # Campaigns
    path('campaign', campaign_views.get_campaigns, name='get_campaigns'),
    path('campaign/create', campaign_views.create_campaign, name='create_campaign'),
    # More specific routes first to avoid matching conflicts
    path('campaign/<int:campaign_id>/instant-launch/', campaign_views.instant_launch_campaign, name='instant_launch_campaign'),
    path('campaign/<int:campaign_id>/run/', campaign_views.run_campaign, name='run_campaign'),
    path('campaign/<int:campaign_id>/report/', campaign_views.download_report, name='download_report'),
    path('campaign/<int:campaign_id>/details/', campaign_views.get_campaign_details, name='get_campaign_details'),
    path('campaign/<int:campaign_id>/voice-assistance/', campaign_views.add_voice_assistance, name='add_voice_assistance'),
    path('campaign/<int:campaign_id>/test-voice/', campaign_views.test_voice, name='test_voice'),
    path('campaign/<int:campaign_id>/update', campaign_views.update_campaign, name='update_campaign'),
    path('campaign/<int:campaign_id>/delete', campaign_views.delete_campaign, name='delete_campaign'),
    path('campaign/<int:campaign_id>/', campaign_views.get_campaign, name='get_campaign'),
    
    # Contacts - order matters: specific routes first
    path('campaign/<int:campaign_id>/contacts/bulk/', campaign_views.add_bulk_contacts, name='add_bulk_contacts'),
    path('campaign/<int:campaign_id>/contacts/', campaign_views.add_contact, name='add_contact'),
    
    # Contact Management
    path('contacts/<int:contact_id>/', campaign_views.get_contact_info, name='get_contact_info'),
    path('contacts/<int:contact_id>/update', campaign_views.update_contact, name='update_contact'),
    path('contacts/<int:contact_id>/attributes/', campaign_views.update_contact_attributes, name='update_contact_attributes'),
    path('contacts/<int:contact_id>/delete/', campaign_views.delete_contact, name='delete_contact'),
    
    # Testing
    path('demo-call/', campaign_views.demo_call, name='demo_call'),
]

