from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin
from django.contrib.auth.models import Group, Permission
from .models import User, Otp, InstituteService, Institute, InstituteModule, Module

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


@admin.register(InstituteService)
class InstituteServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('name',)
    
    fieldsets = (
        (None, {'fields': ('name', 'icon', 'description')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'address', 'created_at')
    search_fields = ('name', 'phone', 'address', 'description')
    list_filter = ('created_at', 'institute_services')
    readonly_fields = ('created_at', 'updated_at', 'location')
    filter_horizontal = ('institute_services',)
    ordering = ('name',)
    
    fieldsets = (
        (None, {'fields': ('name', 'description')}),
        ('Contact Information', {'fields': ('phone', 'address')}),
        ('Location', {'fields': ('latitude', 'longitude', 'location')}),
        ('Media', {'fields': ('logo',)}),
        ('Services', {'fields': ('institute_services',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        (None, {'fields': ('name', 'slug')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(InstituteModule)
class InstituteModuleAdmin(admin.ModelAdmin):
    list_display = ('institute', 'module', 'user_count', 'created_at')
    search_fields = ('institute__name', 'module__name')
    list_filter = ('institute', 'module', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'user_count')
    filter_horizontal = ('users',)
    ordering = ('institute__name', 'module__name')
    
    fieldsets = (
        (None, {'fields': ('institute', 'module')}),
        ('Users', {'fields': ('users', 'user_count')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('institute', 'module').prefetch_related('users')

