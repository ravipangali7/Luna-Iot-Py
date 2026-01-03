from django.contrib import admin
from phone_call.models import PhoneBook, PhoneBookNumber


@admin.register(PhoneBook)
class PhoneBookAdmin(admin.ModelAdmin):
    """Admin interface for PhoneBook model"""
    list_display = ['id', 'name', 'user', 'institute', 'numbers_count', 'created_at']
    list_filter = ['created_at', 'user', 'institute']
    search_fields = ['name', 'user__name', 'user__phone', 'institute__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'user', 'institute')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def numbers_count(self, obj):
        """Display count of numbers in phone book"""
        return obj.numbers.count()
    numbers_count.short_description = 'Numbers'


@admin.register(PhoneBookNumber)
class PhoneBookNumberAdmin(admin.ModelAdmin):
    """Admin interface for PhoneBookNumber model"""
    list_display = ['id', 'name', 'phone', 'phonebook', 'created_at']
    list_filter = ['created_at', 'phonebook']
    search_fields = ['name', 'phone', 'phonebook__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('phonebook', 'name', 'phone')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

