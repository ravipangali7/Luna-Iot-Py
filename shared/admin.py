from django.contrib import admin
from .models import Notification, UserNotification, Popup, Recharge, Geofence, GeofenceUser, GeofenceEvent, ExternalAppLink, SimBalance, SimFreeResource

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

@admin.register(ExternalAppLink)
class ExternalAppLinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'link', 'username', 'createdAt', 'updatedAt')
    list_filter = ('createdAt', 'updatedAt')
    search_fields = ('name', 'link', 'username')
    readonly_fields = ('createdAt', 'updatedAt')


class SimFreeResourceInline(admin.TabularInline):
    model = SimFreeResource
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('name', 'resource_type', 'remaining', 'expiry', 'created_at', 'updated_at')


@admin.register(SimBalance)
class SimBalanceAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'device', 'state', 'balance', 'balance_expiry', 'last_synced_at', 'created_at')
    list_filter = ('state', 'balance_expiry', 'created_at')
    search_fields = ('phone_number', 'device__imei', 'device__phone')
    readonly_fields = ('last_synced_at', 'created_at', 'updated_at')
    inlines = [SimFreeResourceInline]


@admin.register(SimFreeResource)
class SimFreeResourceAdmin(admin.ModelAdmin):
    list_display = ('sim_balance', 'name', 'resource_type', 'remaining', 'expiry', 'created_at')
    list_filter = ('resource_type', 'expiry', 'created_at')
    search_fields = ('name', 'sim_balance__phone_number')
    readonly_fields = ('created_at', 'updated_at')
