from django.db import models
from core.models import User
from decimal import Decimal


class Transaction(models.Model):
    """Transaction model for tracking wallet operations"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    wallet = models.ForeignKey(
        'Wallet', 
        on_delete=models.CASCADE, 
        related_name='transactions',
        db_column='wallet_id'
    )
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Transaction amount"
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text="Type of transaction"
    )
    balance_before = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Wallet balance before transaction"
    )
    balance_after = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Wallet balance after transaction"
    )
    description = models.TextField(
        blank=True, 
        null=True,
        help_text="Description or reason for transaction"
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performed_transactions',
        help_text="Admin user who performed this transaction"
    )
    transaction_reference = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique reference for this transaction"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='COMPLETED',
        help_text="Transaction status"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_column='created_at',
        help_text="Transaction creation timestamp"
    )

    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['performed_by']),
        ]

    def __str__(self):
        return f"Transaction {self.id} - {self.transaction_type} {self.amount} for Wallet {self.wallet.id}"

    def is_credit(self):
        """Check if this is a credit transaction"""
        return self.transaction_type == 'CREDIT'

    def is_debit(self):
        """Check if this is a debit transaction"""
        return self.transaction_type == 'DEBIT'

    def get_amount_display(self):
        """Get formatted amount with sign"""
        if self.is_credit():
            return f"+{self.amount}"
        else:
            return f"-{self.amount}"

    def get_balance_change(self):
        """Get the balance change amount"""
        return self.balance_after - self.balance_before

    @classmethod
    def create_transaction(cls, wallet, amount, transaction_type, description=None, performed_by=None, status='COMPLETED'):
        """Create a new transaction with proper balance tracking"""
        balance_before = wallet.balance
        balance_after = balance_before + (amount if transaction_type == 'CREDIT' else -amount)
        
        # Generate unique reference
        import uuid
        transaction_reference = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        
        transaction = cls.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type=transaction_type,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
            performed_by=performed_by,
            transaction_reference=transaction_reference,
            status=status
        )
        
        return transaction
