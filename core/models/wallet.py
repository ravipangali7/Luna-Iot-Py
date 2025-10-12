from django.db import models
from .user import User


class Wallet(models.Model):
    """Wallet model for user balance management"""
    id = models.BigAutoField(primary_key=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='wallet',
        db_column='user_id'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

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
        """
        Get the current wallet balance
        """
        return float(self.balance)

    def update_balance(self, new_balance):
        """
        Update the wallet balance
        """
        try:
            self.balance = new_balance
            self.save()
            return True
        except Exception as e:
            print(f"Error updating wallet balance: {str(e)}")
            return False

    def add_balance(self, amount):
        """
        Add amount to current balance
        """
        try:
            self.balance += amount
            self.save()
            return True
        except Exception as e:
            print(f"Error adding to wallet balance: {str(e)}")
            return False

    def subtract_balance(self, amount):
        """
        Subtract amount from current balance
        """
        try:
            if self.balance >= amount:
                self.balance -= amount
                self.save()
                return True
            else:
                return False  # Insufficient balance
        except Exception as e:
            print(f"Error subtracting from wallet balance: {str(e)}")
            return False
