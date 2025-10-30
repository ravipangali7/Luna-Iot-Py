from django.urls import path
from shared.views.short_link_api import resolve_short_link


urlpatterns = [
    path("api/shared/short-links/<str:code>", resolve_short_link, name="shared.short_link.resolve"),
]


