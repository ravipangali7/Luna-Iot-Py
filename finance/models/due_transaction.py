from django.db import models
from core.models import User, Institute
from decimal import Decimal
from fleet.models import Vehicle


class DueTransaction(models.Model):
    """Model for tracking due transactions (bills/invoices)"""
    
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='due_transactions',
        db_column='user_id',
        help_text="User who owes this due"
    )
    paid_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paid_transactions',
        db_column='paid_by_id',
        help_text="User who paid for this transaction"
    )
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_column='subtotal',
        help_text="Subtotal amount before VAT"
    )
    vat = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_column='vat',
        help_text="VAT amount"
    )
    total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_column='total',
        help_text="Total amount including VAT"
    )
    renew_date = models.DateTimeField(
        db_column='renew_date',
        help_text="Renewal date for this transaction"
    )
    expire_date = models.DateTimeField(
        db_column='expire_date',
        help_text="Expiration date for this transaction"
    )
    is_paid = models.BooleanField(
        default=False,
        db_column='is_paid',
        help_text="Whether this due has been paid"
    )
    pay_date = models.DateTimeField(
        null=True,
        blank=True,
        db_column='pay_date',
        help_text="Date when payment was made"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_column='created_at',
        help_text="Transaction creation timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_column='updated_at',
        help_text="Last update timestamp"
    )

    class Meta:
        db_table = 'due_transactions'
        verbose_name = 'Due Transaction'
        verbose_name_plural = 'Due Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_paid']),
            models.Index(fields=['expire_date']),
            models.Index(fields=['created_at']),
            models.Index(fields=['paid_by']),
        ]

    def __str__(self):
        return f"Due Transaction {self.id} - User {self.user.id} - {self.total} ({'Paid' if self.is_paid else 'Unpaid'})"

    def calculate_totals(self):
        """Calculate VAT and total from subtotal"""
        from core.models import MySetting
        
        try:
            setting = MySetting.objects.first()
            vat_percent = Decimal(str(setting.vat_percent)) if setting and setting.vat_percent else Decimal('0.00')
        except:
            vat_percent = Decimal('0.00')
        
        # Ensure subtotal is Decimal
        if not isinstance(self.subtotal, Decimal):
            self.subtotal = Decimal(str(self.subtotal))
        
        vat_amount = (self.subtotal * vat_percent) / Decimal('100')
        total_amount = self.subtotal + vat_amount
        
        self.vat = vat_amount
        self.total = total_amount
        return self


class DueTransactionParticular(models.Model):
    """Model for individual line items in a due transaction"""
    
    TYPE_CHOICES = [
        ('vehicle', 'Vehicle'),
        ('parent', 'Parent'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    due_transaction = models.ForeignKey(
        DueTransaction,
        on_delete=models.CASCADE,
        related_name='particulars',
        db_column='due_transaction_id',
        help_text="The due transaction this particular belongs to"
    )
    particular = models.TextField(
        db_column='particular',
        help_text="Description of this particular item"
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        db_column='type',
        help_text="Type of particular (vehicle or parent)"
    )
    institute = models.ForeignKey(
        Institute,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='due_transaction_particulars',
        db_column='institute_id',
        help_text="Institute associated with this particular (for parent type)"
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='due_transaction_particulars',
        db_column='vehicle_id',
        help_text="Vehicle associated with this particular (for vehicle type)"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_column='amount',
        help_text="Unit amount for this particular (customer price)"
    )
    dealer_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        db_column='dealer_amount',
        help_text="Dealer price for this particular"
    )
    quantity = models.IntegerField(
        default=1,
        db_column='quantity',
        help_text="Quantity of this particular"
    )
    total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_column='total',
        help_text="Total amount (amount * quantity)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_column='created_at',
        help_text="Particular creation timestamp"
    )

    class Meta:
        db_table = 'due_transaction_particulars'
        verbose_name = 'Due Transaction Particular'
        verbose_name_plural = 'Due Transaction Particulars'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['due_transaction']),
            models.Index(fields=['type']),
            models.Index(fields=['institute']),
            models.Index(fields=['vehicle']),
        ]

    def __str__(self):
        return f"Particular {self.id} - {self.particular} - {self.total}"

    def save(self, *args, **kwargs):
        """Calculate total before saving"""
        self.total = self.amount * Decimal(str(self.quantity))
        super().save(*args, **kwargs)

