from django.db import models
from core.models import User
from decimal import Decimal
import json


class PaymentTransaction(models.Model):
    """Payment Transaction model for tracking ConnectIPS payment gateway transactions"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('ERROR', 'Error'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payment_transactions',
        db_column='user_id',
        help_text="User who initiated the payment"
    )
    wallet = models.ForeignKey(
        'Wallet',
        on_delete=models.CASCADE,
        related_name='payment_transactions',
        db_column='wallet_id',
        help_text="Wallet to be credited"
    )
    txn_id = models.CharField(
        max_length=100,
        unique=True,
        db_column='txn_id',
        help_text="Transaction ID from ConnectIPS (TXNID)"
    )
    reference_id = models.CharField(
        max_length=100,
        db_column='reference_id',
        help_text="Internal reference ID"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        db_column='amount',
        help_text="Transaction amount in NPR (not paisa)"
    )
    amount_paisa = models.BigIntegerField(
        db_column='amount_paisa',
        help_text="Transaction amount in paisa (for ConnectIPS)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_column='status',
        help_text="Payment transaction status"
    )
    connectips_response = models.JSONField(
        null=True,
        blank=True,
        db_column='connectips_response',
        help_text="Response from ConnectIPS validation API"
    )
    connectips_txn_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_column='connectips_txn_id',
        help_text="NCHL's transaction ID from ConnectIPS"
    )
    connectips_batch_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_column='connectips_batch_id',
        help_text="NCHL's batch ID from ConnectIPS"
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        db_column='error_message',
        help_text="Error message if payment failed"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_column='created_at',
        help_text="Payment transaction creation timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_column='updated_at',
        help_text="Last update timestamp"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        db_column='completed_at',
        help_text="Payment completion timestamp"
    )

    class Meta:
        db_table = 'payment_transactions'
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['wallet']),
            models.Index(fields=['txn_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Payment {self.id} - {self.txn_id} - {self.amount} NPR ({self.status})"
    
    def mark_success(self, connectips_response=None):
        """Mark payment as successful"""
        from django.utils import timezone
        self.status = 'SUCCESS'
        if connectips_response:
            self.connectips_response = connectips_response
            # Extract ConnectIPS transaction details if available
            if isinstance(connectips_response, dict):
                self.connectips_txn_id = connectips_response.get('txnId')
                self.connectips_batch_id = connectips_response.get('batchId')
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message=None):
        """Mark payment as failed"""
        from django.utils import timezone
        self.status = 'FAILED'
        if error_message:
            self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()
    
    def mark_error(self, error_message=None):
        """Mark payment as error"""
        from django.utils import timezone
        self.status = 'ERROR'
        if error_message:
            self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()
    
    def is_successful(self):
        """Check if payment is successful"""
        return self.status == 'SUCCESS'
    
    def is_pending(self):
        """Check if payment is pending"""
        return self.status == 'PENDING'

