from django.urls import path
from .views.share_track_views import (
    create_share_track,
    get_existing_share_track,
    delete_share_track,
    get_my_share_tracks,
    get_share_track_by_token,
)

urlpatterns = [
    path('create/', create_share_track, name='create_share_track'),
    path('existing/<str:imei>/', get_existing_share_track, name='get_existing_share_track'),
    path('delete/<str:imei>/', delete_share_track, name='delete_share_track'),
    path('my-tracks/', get_my_share_tracks, name='get_my_share_tracks'),
    path('<str:token>/', get_share_track_by_token, name='get_share_track_by_token'),
]
