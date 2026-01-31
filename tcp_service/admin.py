from django.contrib import admin
from .models import DashcamLocation, DashcamStatus, DashcamStream, DashcamConnection


@admin.register(DashcamLocation)
class DashcamLocationAdmin(admin.ModelAdmin):
    list_display = ['imei', 'latitude', 'longitude', 'speed', 'direction', 'created_at']
    list_filter = ['imei', 'created_at']
    search_fields = ['imei']
    ordering = ['-created_at']


@admin.register(DashcamStatus)
class DashcamStatusAdmin(admin.ModelAdmin):
    list_display = ['imei', 'battery', 'signal', 'recording', 'sd_status', 'created_at']
    list_filter = ['imei', 'recording', 'sd_status']
    search_fields = ['imei']
    ordering = ['-created_at']


@admin.register(DashcamStream)
class DashcamStreamAdmin(admin.ModelAdmin):
    list_display = ['imei', 'channel', 'is_streaming', 'viewer_count', 'started_at']
    list_filter = ['imei', 'channel', 'is_streaming']
    search_fields = ['imei', 'stream_key']
    ordering = ['-created_at']


@admin.register(DashcamConnection)
class DashcamConnectionAdmin(admin.ModelAdmin):
    list_display = ['imei', 'phone', 'is_connected', 'last_heartbeat', 'ip_address']
    list_filter = ['is_connected']
    search_fields = ['imei', 'phone']
    ordering = ['-created_at']
