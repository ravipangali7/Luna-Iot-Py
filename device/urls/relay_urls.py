"""
Relay URL patterns
Matches Node.js relay routes exactly
"""
from django.urls import path
from device.views import relay_views

urlpatterns = [
    # Relay control routes
    path('turn-on', relay_views.turn_on_relay, name='turn_on_relay'),
    path('turn-off', relay_views.turn_off_relay, name='turn_off_relay'),
]
