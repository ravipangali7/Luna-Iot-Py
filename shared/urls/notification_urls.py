from django.urls import path
from shared.views import notification_views

urlpatterns = [
    path('notification', notification_views.get_notifications, name='get_notifications'),
    path('notification/create', notification_views.create_notification, name='create_notification'),
    path('notification/<int:id>', notification_views.delete_notification, name='delete_notification'),
    path('notification/<int:notification_id>/read', notification_views.mark_notification_as_read, name='mark_notification_as_read'),
    path('notification/unread/count', notification_views.get_unread_notification_count, name='get_unread_notification_count'),
]
