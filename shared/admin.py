from django.contrib import admin
from .models import Notification, UserNotification, Popup, Recharge, Geofence, GeofenceUser, GeofenceEvent

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'sentBy', 'createdAt')
    list_filter = ('type', 'createdAt')
    search_fields = ('title', 'message', 'sentBy__name')
    readonly_fields = ('createdAt',)

@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification', 'isRead', 'createdAt')
    list_filter = ('isRead', 'createdAt')
    search_fields = ('user__name', 'notification__title')

@admin.register(Popup)
class PopupAdmin(admin.ModelAdmin):
    list_display = ('title', 'isActive', 'createdAt', 'updatedAt')
    list_filter = ('isActive', 'createdAt')
    search_fields = ('title', 'message')

@admin.register(Recharge)
class RechargeAdmin(admin.ModelAdmin):
    list_display = ('device', 'amount', 'createdAt')
    list_filter = ('createdAt',)
    search_fields = ('device__imei',)

@admin.register(Geofence)
class GeofenceAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'createdAt', 'updatedAt')
    list_filter = ('type', 'createdAt')
    search_fields = ('title',)

@admin.register(GeofenceUser)
class GeofenceUserAdmin(admin.ModelAdmin):
    list_display = ('geofence', 'user', 'createdAt')
    list_filter = ('createdAt',)
    search_fields = ('geofence__title', 'user__name')

@admin.register(GeofenceEvent)
class GeofenceEventAdmin(admin.ModelAdmin):
    list_display = ('vehicle_id', 'geofence_id', 'is_inside', 'last_event_type', 'last_event_at', 'createdAt')
    list_filter = ('is_inside', 'last_event_type', 'last_event_at', 'createdAt')
    search_fields = ('vehicle_id', 'geofence_id')
    readonly_fields = ('createdAt', 'updatedAt')
