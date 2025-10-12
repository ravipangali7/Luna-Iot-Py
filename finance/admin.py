from django.contrib import admin
from finance.models import Wallet, Transaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'balance', 'created_at', 'updated_at')
    search_fields = ('user__name', 'user__phone', 'user__username')
    list_filter = ('created_at', 'updated_at', 'user__is_active')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('user', 'balance')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'wallet', 'amount', 'transaction_type', 'balance_after', 
        'performed_by', 'status', 'created_at'
    )
    list_filter = (
        'transaction_type', 'status', 'created_at', 'performed_by'
    )
    search_fields = (
        'wallet__user__name', 'wallet__user__phone', 'description',
        'transaction_reference', 'performed_by__name'
    )
    readonly_fields = (
        'id', 'transaction_reference', 'balance_before', 'balance_after', 'created_at'
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('wallet', 'amount', 'transaction_type', 'description')
        }),
        ('Balance Tracking', {
            'fields': ('balance_before', 'balance_after'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('performed_by', 'status', 'transaction_reference'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'wallet__user', 'performed_by'
        )
    
    def has_add_permission(self, request):
        # Only allow adding transactions through the API
        return False
    
    def has_change_permission(self, request, obj=None):
        # Only allow viewing transactions
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of transactions for audit trail
        return False