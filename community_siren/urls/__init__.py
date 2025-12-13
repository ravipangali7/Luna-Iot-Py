from django.urls import path, include

urlpatterns = [
    # Community Siren Buzzer routes
    path('community-siren-buzzer/', include('community_siren.urls.community_siren_buzzer_urls')),
    
    # Community Siren Switch routes
    path('community-siren-switch/', include('community_siren.urls.community_siren_switch_urls')),
    
    # Community Siren Members routes
    path('community-siren-members/', include('community_siren.urls.community_siren_members_urls')),
    
    # Community Siren Contact routes
    path('community-siren-contact/', include('community_siren.urls.community_siren_contact_urls')),
    
    # Community Siren History routes
    path('community-siren-history/', include('community_siren.urls.community_siren_history_urls')),
]
