from django.urls import path
from shared.views.short_link_api import resolve_short_link


urlpatterns = [
    # This module is included under project prefix 'api/shared/', so keep only 'short-links/...'
    path("short-links/<str:code>", resolve_short_link, name="shared.short_link.resolve"),
]


