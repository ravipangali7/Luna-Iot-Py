from django.db import models
from core.models import User
from decimal import Decimal


class Wallet(models.Model):
    """Wallet model for user balance management with transaction tracking"""
    
    id = models.BigAutoField(primary_key=True)
    balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Current wallet balance"
    )
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='wallet',
        db_column='user_id',
        help_text="User who owns this wallet"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        db_column='created_at',
        help_text="Wallet creation timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        db_column='updated_at',
        help_text="Last wallet update timestamp"
    )

    class Meta:
        db_table = 'wallets'
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Wallet for {self.user.name or self.user.phone} (Balance: {self.balance})"

    def get_balance(self):
        """Get the current wallet balance as float"""
        return float(self.balance)

    def update_balance(self, new_balance, description=None, performed_by=None):
        """
        Update the wallet balance and create a transaction record
        """
        try:
            old_balance = self.balance
            self.balance = Decimal(str(new_balance))
            self.save()
            
            # Create transaction record
            from .transaction import Transaction
            transaction_type = 'CREDIT' if new_balance > old_balance else 'DEBIT'
            amount = abs(new_balance - old_balance)
            
            if amount > 0:  # Only create transaction if there's a change
                Transaction.create_transaction(
                    wallet=self,
                    amount=amount,
                    transaction_type=transaction_type,
                    description=description or f"Balance updated from {old_balance} to {new_balance}",
                    performed_by=performed_by
                )
            
            return True
        except Exception as e:
            print(f"Error updating wallet balance: {str(e)}")
            return False

    def add_balance(self, amount, description=None, performed_by=None):
        """
        Add amount to current balance and create transaction record
        """
        try:
            from .transaction import Transaction
            
            # Create transaction first
            transaction = Transaction.create_transaction(
                wallet=self,
                amount=Decimal(str(amount)),
                transaction_type='CREDIT',
                description=description or f"Balance added: {amount}",
                performed_by=performed_by
            )
            
            # Update balance
            self.balance += Decimal(str(amount))
            self.save()
            
            # Update transaction with actual balance after
            transaction.balance_after = self.balance
            transaction.save()
            
            return True
        except Exception as e:
            print(f"Error adding to wallet balance: {str(e)}")
            return False

    def subtract_balance(self, amount, description=None, performed_by=None):
        """
        Subtract amount from current balance and create transaction record
        """
        try:
            amount_decimal = Decimal(str(amount))
            
            if self.balance < amount_decimal:
                return False  # Insufficient balance
            
            from .transaction import Transaction
            
            # Create transaction first
            transaction = Transaction.create_transaction(
                wallet=self,
                amount=amount_decimal,
                transaction_type='DEBIT',
                description=description or f"Balance deducted: {amount}",
                performed_by=performed_by
            )
            
            # Update balance
            self.balance -= amount_decimal
            self.save()
            
            # Update transaction with actual balance after
            transaction.balance_after = self.balance
            transaction.save()
            
            return True
        except Exception as e:
            print(f"Error subtracting from wallet balance: {str(e)}")
            return False

    def get_transaction_history(self, limit=None):
        """
        Get transaction history for this wallet
        """
        transactions = self.transactions.all()
        if limit:
            transactions = transactions[:limit]
        return transactions

    def get_recent_transactions(self, count=10):
        """
        Get recent transactions for this wallet
        """
        return self.transactions.all()[:count]

    def get_balance_change_today(self):
        """
        Get total balance change for today
        """
        from django.utils import timezone
        from datetime import date
        
        today = timezone.now().date()
        today_transactions = self.transactions.filter(created_at__date=today)
        
        credit_total = sum(t.amount for t in today_transactions.filter(transaction_type='CREDIT'))
        debit_total = sum(t.amount for t in today_transactions.filter(transaction_type='DEBIT'))
        
        return {
            'credit': float(credit_total),
            'debit': float(debit_total),
            'net_change': float(credit_total - debit_total)
        }
