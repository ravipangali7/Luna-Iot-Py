from django.contrib import admin
from finance.models import Wallet, Transaction, DueTransaction, DueTransactionParticular


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'balance', 'call_price', 'sms_price', 'created_at', 'updated_at')
    search_fields = ('user__name', 'user__phone', 'user__username')
    list_filter = ('created_at', 'updated_at', 'user__is_active')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('user', 'balance')}),
        ('Pricing', {'fields': ('call_price', 'sms_price')}),
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


class DueTransactionParticularInline(admin.TabularInline):
    """Inline admin for DueTransactionParticular"""
    model = DueTransactionParticular
    extra = 0
    readonly_fields = ('id', 'total', 'created_at')
    fields = ('particular', 'type', 'institute', 'amount', 'quantity', 'total', 'created_at')


@admin.register(DueTransaction)
class DueTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'subtotal', 'vat', 'total', 'is_paid', 
        'renew_date', 'expire_date', 'pay_date', 'created_at'
    )
    list_filter = ('is_paid', 'created_at', 'expire_date', 'renew_date')
    search_fields = (
        'user__name', 'user__phone', 'user__username', 'id'
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [DueTransactionParticularInline]
    
    fieldsets = (
        (None, {
            'fields': ('user', 'is_paid', 'pay_date')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'vat', 'total')
        }),
        ('Dates', {
            'fields': ('renew_date', 'expire_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('particulars')


@admin.register(DueTransactionParticular)
class DueTransactionParticularAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'due_transaction', 'particular', 'type', 'institute',
        'amount', 'quantity', 'total', 'created_at'
    )
    list_filter = ('type', 'created_at', 'institute')
    search_fields = (
        'particular', 'due_transaction__id', 'due_transaction__user__name',
        'due_transaction__user__phone'
    )
    readonly_fields = ('id', 'total', 'created_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('due_transaction', 'particular', 'type', 'institute')
        }),
        ('Pricing', {
            'fields': ('amount', 'quantity', 'total')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'due_transaction__user', 'institute'
        )