from django.urls import path
from shared.views.short_link import redirect_short_link


urlpatterns = [
    path("g/<str:code>", redirect_short_link, name="shared.short_link"),
]


