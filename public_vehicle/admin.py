from django.contrib import admin
from public_vehicle.models import PublicVehicle, PublicVehicleImage


class PublicVehicleImageInline(admin.TabularInline):
    model = PublicVehicleImage
    extra = 1
    fields = ['image', 'order']


@admin.register(PublicVehicle)
class PublicVehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'institute', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'institute']
    search_fields = ['institute__name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PublicVehicleImageInline]


@admin.register(PublicVehicleImage)
class PublicVehicleImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'public_vehicle', 'order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['public_vehicle__institute__name']

