from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from .models import (
    User, Role, Permission, RolePermission, Device, Vehicle, Location, 
    Status, UserDevice, UserVehicle, Otp, Notification, UserNotification,
    Geofence, GeofenceVehicle, GeofenceUser, Popup
)

# Custom admin site header and title
admin.site.site_header = "Luna IoT Admin"
admin.site.site_title = "Luna IoT Admin Portal"
admin.site.index_title = "Welcome to Luna IoT Administration"

# Inline classes
class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1
    autocomplete_fields = ['permission']

class UserDeviceInline(admin.TabularInline):
    model = UserDevice
    extra = 1
    autocomplete_fields = ['user', 'device']

class UserVehicleInline(admin.TabularInline):
    model = UserVehicle
    extra = 1
    autocomplete_fields = ['user', 'vehicle']

class GeofenceVehicleInline(admin.TabularInline):
    model = GeofenceVehicle
    extra = 1
    autocomplete_fields = ['vehicle']

class GeofenceUserInline(admin.TabularInline):
    model = GeofenceUser
    extra = 1
    autocomplete_fields = ['user']

class UserNotificationInline(admin.TabularInline):
    model = UserNotification
    extra = 1
    autocomplete_fields = ['user', 'notification']

# User Admin
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'status', 'role', 'created_at', 'updated_at']
    list_filter = ['status', 'role', 'created_at', 'updated_at']
    search_fields = ['name', 'phone', 'token']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['role']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'phone', 'password', 'status', 'role')
        }),
        ('Authentication', {
            'fields': ('token', 'fcm_token')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Role Admin
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'description']
    list_per_page = 25
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [RolePermissionInline]
    
    fieldsets = (
        ('Role Information', {
            'fields': ('name', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Permission Admin
@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'description']
    list_per_page = 25
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Permission Information', {
            'fields': ('name', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# RolePermission Admin
@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'role', 'permission', 'created_at']
    list_filter = ['role', 'permission', 'created_at']
    search_fields = ['role__name', 'permission__name']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    autocomplete_fields = ['role', 'permission']

# Device Admin
@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['id', 'imei', 'phone', 'sim', 'protocol', 'model', 'created_at', 'updated_at']
    list_filter = ['sim', 'protocol', 'model', 'created_at', 'updated_at']
    search_fields = ['imei', 'phone', 'iccid']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [UserDeviceInline]
    
    fieldsets = (
        ('Device Information', {
            'fields': ('imei', 'phone', 'sim', 'protocol', 'iccid', 'model')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Vehicle Admin
@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'vehicle_no', 'vehicle_type', 'imei', 'odometer', 'mileage', 'speed_limit', 'created_at']
    list_filter = ['vehicle_type', 'created_at', 'updated_at']
    search_fields = ['name', 'vehicle_no', 'imei', 'device__imei']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['device']
    inlines = [UserVehicleInline, GeofenceVehicleInline]
    
    fieldsets = (
        ('Vehicle Information', {
            'fields': ('imei', 'device', 'name', 'vehicle_no', 'vehicle_type')
        }),
        ('Technical Details', {
            'fields': ('odometer', 'mileage', 'minimum_fuel', 'speed_limit')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Location Admin
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['id', 'imei', 'device', 'latitude', 'longitude', 'speed', 'course', 'real_time_gps', 'satellite', 'created_at']
    list_filter = ['real_time_gps', 'created_at', 'device__sim', 'device__protocol']
    search_fields = ['imei', 'device__imei']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    autocomplete_fields = ['device']
    
    fieldsets = (
        ('Location Information', {
            'fields': ('device', 'imei', 'latitude', 'longitude')
        }),
        ('GPS Details', {
            'fields': ('speed', 'course', 'real_time_gps', 'satellite')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

# Status Admin
@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'imei', 'device', 'battery', 'signal', 'ignition', 'charging', 'relay', 'created_at']
    list_filter = ['ignition', 'charging', 'relay', 'created_at', 'device__sim', 'device__protocol']
    search_fields = ['imei', 'device__imei']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    autocomplete_fields = ['device']
    
    fieldsets = (
        ('Device Status', {
            'fields': ('device', 'imei', 'battery', 'signal')
        }),
        ('System Status', {
            'fields': ('ignition', 'charging', 'relay')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

# UserDevice Admin
@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'device', 'created_at']
    list_filter = ['created_at', 'user__status', 'device__sim']
    search_fields = ['user__name', 'user__phone', 'device__imei']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    autocomplete_fields = ['user', 'device']

# UserVehicle Admin
@admin.register(UserVehicle)
class UserVehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'vehicle', 'is_main', 'all_access', 'live_tracking', 'history', 'report', 'created_at']
    list_filter = ['is_main', 'all_access', 'live_tracking', 'history', 'report', 'created_at', 'user__status', 'vehicle__vehicle_type']
    search_fields = ['user__name', 'user__phone', 'vehicle__name', 'vehicle__vehicle_no']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    autocomplete_fields = ['user', 'vehicle']
    
    fieldsets = (
        ('User-Vehicle Relationship', {
            'fields': ('user', 'vehicle', 'is_main')
        }),
        ('Permissions', {
            'fields': ('all_access', 'live_tracking', 'history', 'report', 'vehicle_profile', 'events', 'geofence', 'edit', 'share_tracking', 'notification')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

# OTP Admin
@admin.register(Otp)
class OtpAdmin(admin.ModelAdmin):
    list_display = ['id', 'phone', 'otp', 'expires_at', 'created_at']
    list_filter = ['expires_at', 'created_at']
    search_fields = ['phone', 'otp']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('OTP Information', {
            'fields': ('phone', 'otp', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

# Notification Admin
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'type', 'sent_by', 'created_at']
    list_filter = ['type', 'created_at', 'sent_by__status']
    search_fields = ['title', 'message', 'sent_by__name', 'sent_by__phone']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    autocomplete_fields = ['sent_by']
    inlines = [UserNotificationInline]
    
    fieldsets = (
        ('Notification Content', {
            'fields': ('title', 'message', 'type')
        }),
        ('Sender Information', {
            'fields': ('sent_by',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

# UserNotification Admin
@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'notification', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at', 'user__status']
    search_fields = ['user__name', 'user__phone', 'notification__title']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    autocomplete_fields = ['user', 'notification']

# Geofence Admin
@admin.register(Geofence)
class GeofenceAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'type', 'created_at', 'updated_at']
    list_filter = ['type', 'created_at', 'updated_at']
    search_fields = ['title']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [GeofenceVehicleInline, GeofenceUserInline]
    
    fieldsets = (
        ('Geofence Information', {
            'fields': ('title', 'type', 'boundary')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# GeofenceVehicle Admin
@admin.register(GeofenceVehicle)
class GeofenceVehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'geofence', 'vehicle', 'created_at']
    list_filter = ['created_at', 'geofence__type', 'vehicle__vehicle_type']
    search_fields = ['geofence__title', 'vehicle__name', 'vehicle__vehicle_no']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    autocomplete_fields = ['geofence', 'vehicle']

# GeofenceUser Admin
@admin.register(GeofenceUser)
class GeofenceUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'geofence', 'user', 'created_at']
    list_filter = ['created_at', 'geofence__type', 'user__status']
    search_fields = ['geofence__title', 'user__name', 'user__phone']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    autocomplete_fields = ['geofence', 'user']

# Popup Admin
@admin.register(Popup)
class PopupAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['title', 'message']
    list_per_page = 25
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Popup Content', {
            'fields': ('title', 'message', 'image')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Custom admin actions
@admin.action(description="Mark selected users as active")
def make_active(modeladmin, request, queryset):
    queryset.update(status='ACTIVE')
make_active.short_description = "Mark selected users as active"

@admin.action(description="Mark selected users as inactive")
def make_inactive(modeladmin, request, queryset):
    queryset.update(status='INACTIVE')
make_inactive.short_description = "Mark selected users as inactive"

@admin.action(description="Mark selected popups as active")
def make_popup_active(modeladmin, request, queryset):
    queryset.update(is_active=True)
make_popup_active.short_description = "Mark selected popups as active"

@admin.action(description="Mark selected popups as inactive")
def make_popup_inactive(modeladmin, request, queryset):
    queryset.update(is_active=False)
make_popup_inactive.short_description = "Mark selected popups as inactive"

# Add actions to respective admin classes
UserAdmin.actions = [make_active, make_inactive]
PopupAdmin.actions = [make_popup_active, make_popup_inactive]