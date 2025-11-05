from django.urls import path
from shared.views.external_app_link_views import get_external_app_links


urlpatterns = [
    path('external-app-links/', get_external_app_links, name='external_app_links'),
]

