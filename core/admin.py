from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin
from django.contrib.auth.models import Group, Permission
from .models import User, Otp

# Unregister default Group admin and register with custom admin
admin.site.unregister(Group)
@admin.register(Group)
class CustomGroupAdmin(GroupAdmin):
    list_display = ('name', 'get_permission_count')
    search_fields = ('name',)
    
    def get_permission_count(self, obj):
        return obj.permissions.count()
    get_permission_count.short_description = 'Permissions Count'

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename', 'content_type')
    search_fields = ('name', 'codename')
    list_filter = ('content_type',)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('phone', 'username', 'name', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('phone', 'username', 'name')
    ordering = ('-date_joined',)
    filter_horizontal = ('user_permissions', 'groups') # For direct user permissions

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal info', {'fields': ('username', 'name', 'fcm_token')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined', 'username')

    # Customizing add_fieldsets for user creation
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'name', 'password1', 'password2', 'is_staff', 'is_superuser', 'is_active', 'fcm_token'),
        }),
    )

    # Ensure 'phone' is used for authentication in admin
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj: # For new user creation
            form.base_fields['phone'].required = True
        return form

@admin.register(Otp)
class OtpAdmin(admin.ModelAdmin):
    list_display = ('phone', 'otp', 'expiresAt', 'createdAt')
    search_fields = ('phone',)
    readonly_fields = ('createdAt',)