from django.db import models
from decimal import Decimal

class MySetting(models.Model):
    id = models.BigAutoField(primary_key=True)
    mypay_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    vat_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        db_column='vat_percent',
        help_text="VAT percentage"
    )
    call_price = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        db_column='call_price',
        help_text="Default call price"
    )
    sms_price = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        db_column='sms_price',
        help_text="Default SMS price"
    )
    sms_character_price = models.IntegerField(
        default=160,
        db_column='sms_character_price',
        help_text="Number of characters per SMS part (default: 160)"
    )
    parent_price = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        db_column='parent_price',
        help_text="Default parent price"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'my_settings'
        verbose_name = 'My Setting'
        verbose_name_plural = 'My Settings'

    def __str__(self):
        return f"MySetting (Balance: {self.mypay_balance})"

    @classmethod
    def get_balance(cls):
        """
        Get the current mypay balance
        Returns the balance from the first (and should be only) record
        """
        try:
            setting = cls.objects.first()
            if setting:
                return float(setting.mypay_balance)
            else:
                # Create initial record if none exists
                setting = cls.objects.create(mypay_balance=0.00)
                return 0.00
        except Exception as e:
            print(f"Error getting mypay balance: {str(e)}")
            return 0.00

    @classmethod
    def update_balance(cls, new_balance):
        """
        Update the mypay balance
        """
        try:
            setting, created = cls.objects.get_or_create(
                defaults={'mypay_balance': new_balance}
            )
            if not created:
                setting.mypay_balance = new_balance
                setting.save()
            return True
        except Exception as e:
            print(f"Error updating mypay balance: {str(e)}")
            return False
