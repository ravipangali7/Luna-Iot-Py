from django.contrib import admin
from .models import (
    AlertType, AlertGeofence, AlertRadar, AlertBuzzer, 
    AlertContact, AlertSwitch, AlertHistory
)


@admin.register(AlertType)
class AlertTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('name',)
    
    fieldsets = (
        (None, {'fields': ('name', 'icon')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(AlertGeofence)
class AlertGeofenceAdmin(admin.ModelAdmin):
    list_display = ('title', 'institute', 'alert_types_count', 'created_at')
    search_fields = ('title', 'institute__name')
    list_filter = ('institute', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('alert_types',)
    ordering = ('title',)
    
    fieldsets = (
        (None, {'fields': ('title', 'institute')}),
        ('Configuration', {'fields': ('boundary', 'alert_types')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def alert_types_count(self, obj):
        return obj.alert_types.count()
    alert_types_count.short_description = 'Alert Types Count'


@admin.register(AlertRadar)
class AlertRadarAdmin(admin.ModelAdmin):
    list_display = ('title', 'institute', 'geofences_count', 'created_at')
    search_fields = ('title', 'institute__name')
    list_filter = ('institute', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('alert_geofences',)
    ordering = ('title',)
    
    fieldsets = (
        (None, {'fields': ('title', 'institute')}),
        ('Configuration', {'fields': ('token', 'alert_geofences')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def geofences_count(self, obj):
        return obj.alert_geofences.count()
    geofences_count.short_description = 'Geofences Count'


@admin.register(AlertBuzzer)
class AlertBuzzerAdmin(admin.ModelAdmin):
    list_display = ('title', 'device', 'institute', 'delay', 'geofences_count', 'created_at')
    search_fields = ('title', 'device__imei', 'institute__name')
    list_filter = ('institute', 'device', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('alert_geofences',)
    ordering = ('title',)
    
    fieldsets = (
        (None, {'fields': ('title', 'device', 'institute')}),
        ('Configuration', {'fields': ('delay', 'alert_geofences')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def geofences_count(self, obj):
        return obj.alert_geofences.count()
    geofences_count.short_description = 'Geofences Count'


@admin.register(AlertContact)
class AlertContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'institute', 'is_sms', 'is_call', 'geofences_count', 'created_at')
    search_fields = ('name', 'phone', 'institute__name')
    list_filter = ('institute', 'is_sms', 'is_call', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('alert_geofences', 'alert_types')
    ordering = ('name',)
    
    fieldsets = (
        (None, {'fields': ('name', 'phone', 'institute')}),
        ('Configuration', {'fields': ('is_sms', 'is_call', 'alert_geofences', 'alert_types')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def geofences_count(self, obj):
        return obj.alert_geofences.count()
    geofences_count.short_description = 'Geofences Count'


@admin.register(AlertSwitch)
class AlertSwitchAdmin(admin.ModelAdmin):
    list_display = ('title', 'device', 'institute', 'trigger', 'primary_phone', 'created_at')
    search_fields = ('title', 'device__imei', 'institute__name', 'primary_phone')
    list_filter = ('institute', 'device', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('title',)
    
    fieldsets = (
        (None, {'fields': ('title', 'device', 'institute')}),
        ('Location', {'fields': ('latitude', 'longitude', 'trigger')}),
        ('Contacts', {'fields': ('primary_phone', 'secondary_phone')}),
        ('Media', {'fields': ('image',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(AlertHistory)
class AlertHistoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'alert_type', 'source', 'status', 'institute', 'datetime', 'created_at')
    search_fields = ('name', 'primary_phone', 'institute__name', 'alert_type__name')
    list_filter = ('source', 'status', 'institute', 'alert_type', 'datetime', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-datetime',)
    
    fieldsets = (
        (None, {'fields': ('name', 'alert_type', 'institute')}),
        ('Contact Information', {'fields': ('primary_phone', 'secondary_phone')}),
        ('Location & Time', {'fields': ('latitude', 'longitude', 'datetime')}),
        ('Details', {'fields': ('source', 'status', 'remarks', 'image')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('alert_type', 'institute')