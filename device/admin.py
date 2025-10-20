from django.contrib import admin
from .models import Device, Location, Status, UserDevice, BuzzerStatus, SosStatus, AlarmData

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('imei', 'phone', 'sim', 'protocol', 'model', 'type', 'createdAt')
    list_filter = ('sim', 'protocol', 'model', 'type', 'createdAt')
    search_fields = ('imei', 'phone')
    readonly_fields = ('createdAt', 'updatedAt')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('device', 'imei', 'latitude', 'longitude', 'speed', 'createdAt')
    list_filter = ('createdAt', 'realTimeGps')
    search_fields = ('imei', 'device__imei')
    readonly_fields = ('createdAt',)

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('device', 'imei', 'battery', 'signal', 'ignition', 'charging', 'relay', 'createdAt')
    list_filter = ('ignition', 'charging', 'relay', 'createdAt')
    search_fields = ('imei', 'device__imei')
    readonly_fields = ('createdAt',)

@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device', 'createdAt')
    list_filter = ('createdAt',)
    search_fields = ('user__name', 'device__imei')

@admin.register(BuzzerStatus)
class BuzzerStatusAdmin(admin.ModelAdmin):
    list_display = ('device', 'imei', 'battery', 'signal', 'ignition', 'charging', 'relay', 'createdAt')
    list_filter = ('ignition', 'charging', 'relay', 'createdAt')
    search_fields = ('imei', 'device__imei')
    readonly_fields = ('createdAt',)

@admin.register(SosStatus)
class SosStatusAdmin(admin.ModelAdmin):
    list_display = ('device', 'imei', 'battery', 'signal', 'ignition', 'charging', 'relay', 'createdAt')
    list_filter = ('ignition', 'charging', 'relay', 'createdAt')
    search_fields = ('imei', 'device__imei')
    readonly_fields = ('createdAt',)

@admin.register(AlarmData)
class AlarmDataAdmin(admin.ModelAdmin):
    list_display = ('device', 'imei', 'alarm', 'latitude', 'longitude', 'speed', 'battery', 'signal', 'createdAt')
    list_filter = ('alarm', 'realTimeGps', 'createdAt')
    search_fields = ('imei', 'device__imei', 'alarm')
    readonly_fields = ('createdAt',)
