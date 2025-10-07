from django.db import models

class MySetting(models.Model):
    id = models.BigAutoField(primary_key=True)
    mypay_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
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
