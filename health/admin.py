from django.contrib import admin
from .models import BloodDonation

@admin.register(BloodDonation)
class BloodDonationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'bloodGroup', 'applyType', 'status', 'createdAt')
    list_filter = ('applyType', 'bloodGroup', 'status', 'createdAt')
    search_fields = ('name', 'phone', 'address')
    readonly_fields = ('createdAt', 'updatedAt')
