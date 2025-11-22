from django.contrib import admin
from .models import (
    Vehicle, UserVehicle, GeofenceVehicle, ShareTrack,
    VehicleServicing, VehicleExpenses, VehicleDocument, VehicleEnergyCost
)

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'vehicleNo', 'vehicleType', 'imei', 'odometer', 'speedLimit', 'createdAt')
    list_filter = ('vehicleType', 'createdAt')
    search_fields = ('name', 'vehicleNo', 'imei')
    readonly_fields = ('createdAt', 'updatedAt')

@admin.register(UserVehicle)
class UserVehicleAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle', 'isMain', 'allAccess', 'liveTracking', 'createdAt')
    list_filter = ('isMain', 'allAccess', 'liveTracking', 'createdAt')
    search_fields = ('user__name', 'vehicle__name')
    filter_horizontal = ()

@admin.register(GeofenceVehicle)
class GeofenceVehicleAdmin(admin.ModelAdmin):
    list_display = ('geofence', 'vehicle', 'createdAt')
    list_filter = ('createdAt',)
    search_fields = ('geofence__title', 'vehicle__name')

@admin.register(ShareTrack)
class ShareTrackAdmin(admin.ModelAdmin):
    list_display = ('imei', 'user', 'token', 'created_at', 'scheduled_for', 'is_active')
    list_filter = ('is_active', 'created_at', 'scheduled_for')
    search_fields = ('imei', 'user__name', 'token')
    readonly_fields = ('token', 'created_at')
    ordering = ('-created_at',)

@admin.register(VehicleServicing)
class VehicleServicingAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'title', 'odometer', 'amount', 'date', 'created_at')
    list_filter = ('date', 'created_at')
    search_fields = ('vehicle__name', 'vehicle__imei', 'title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-date', '-created_at')

@admin.register(VehicleExpenses)
class VehicleExpensesAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'title', 'expenses_type', 'amount', 'entry_date', 'created_at')
    list_filter = ('expenses_type', 'entry_date', 'created_at')
    search_fields = ('vehicle__name', 'vehicle__imei', 'title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-entry_date', '-created_at')

@admin.register(VehicleDocument)
class VehicleDocumentAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'title', 'last_expire_date', 'expire_in_month', 'created_at')
    list_filter = ('title', 'last_expire_date', 'created_at')
    search_fields = ('vehicle__name', 'vehicle__imei', 'title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-last_expire_date', '-created_at')

@admin.register(VehicleEnergyCost)
class VehicleEnergyCostAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'title', 'energy_type', 'amount', 'total_unit', 'entry_date', 'created_at')
    list_filter = ('energy_type', 'entry_date', 'created_at')
    search_fields = ('vehicle__name', 'vehicle__imei', 'title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-entry_date', '-created_at')
