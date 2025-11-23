from django.contrib import admin
from garbage.models import GarbageVehicle


@admin.register(GarbageVehicle)
class GarbageVehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'institute', 'vehicle', 'created_at']
    list_filter = ['created_at', 'institute']
    search_fields = ['institute__name', 'vehicle__name', 'vehicle__vehicleNo']
    readonly_fields = ['created_at', 'updated_at']

