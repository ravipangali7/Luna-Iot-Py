from django.contrib import admin
from .models import Vehicle, UserVehicle, GeofenceVehicle

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
