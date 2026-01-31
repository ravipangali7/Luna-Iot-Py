"""
WebSocket URL Routing for Dashcam Video Streaming
"""
from django.urls import re_path
from .consumer import DashcamVideoConsumer

websocket_urlpatterns = [
    re_path(r'ws/dashcam/$', DashcamVideoConsumer.as_asgi()),
    re_path(r'ws/dashcam/(?P<imei>\w+)/$', DashcamVideoConsumer.as_asgi()),
]
