from django.contrib import admin
from .models import (
    SchoolBus, SchoolParent, SchoolSMS
)


@admin.register(SchoolBus)
class SchoolBusAdmin(admin.ModelAdmin):
    list_display = ('institute', 'bus', 'created_at')
    search_fields = ('institute__name', 'bus__name', 'bus__vehicleNo')
    list_filter = ('institute', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('institute', 'bus')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(SchoolParent)
class SchoolParentAdmin(admin.ModelAdmin):
    list_display = ('parent', 'latitude', 'longitude', 'buses_count', 'created_at')
    search_fields = ('parent__name', 'parent__phone')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('school_buses',)
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('parent', 'school_buses')}),
        ('Location', {'fields': ('latitude', 'longitude')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def buses_count(self, obj):
        return obj.school_buses.count()
    buses_count.short_description = 'Buses Count'


@admin.register(SchoolSMS)
class SchoolSMSAdmin(admin.ModelAdmin):
    list_display = ('institute', 'message_preview', 'phone_numbers_count', 'created_at')
    search_fields = ('message', 'institute__name')
    list_filter = ('institute', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'phone_numbers_count')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('institute', 'message')}),
        ('Phone Numbers', {'fields': ('phone_numbers', 'phone_numbers_count')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def message_preview(self, obj):
        if obj.message and len(obj.message) > 50:
            return obj.message[:50] + "..."
        return obj.message or ""
    message_preview.short_description = 'Message'
    
    def phone_numbers_count(self, obj):
        return len(obj.phone_numbers) if obj.phone_numbers else 0
    phone_numbers_count.short_description = 'Phone Numbers Count'

