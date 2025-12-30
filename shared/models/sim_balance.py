from django.db import models
from device.models import Device


class SimBalance(models.Model):
    """Model to store SIM balance information for devices"""
    id = models.BigAutoField(primary_key=True)
    device = models.OneToOneField(
        Device, 
        on_delete=models.CASCADE, 
        related_name='sim_balance',
        null=True,
        blank=True,
        help_text="Linked device (can be null if device not found during import)"
    )
    phone_number = models.CharField(max_length=20, db_index=True, help_text="Phone number (SIM number)")
    state = models.CharField(max_length=20, default='ACTIVE', help_text="SIM state (ACTIVE, INACTIVE, etc.)")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Account balance")
    balance_expiry = models.DateTimeField(null=True, blank=True, help_text="Balance expiry date")
    last_synced_at = models.DateTimeField(auto_now=True, db_column='last_synced_at', help_text="Last sync timestamp")
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'sim_balances'
        verbose_name = 'SIM Balance'
        verbose_name_plural = 'SIM Balances'
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['balance_expiry']),
            models.Index(fields=['state']),
        ]
    
    def __str__(self):
        device_info = f"Device {self.device.imei}" if self.device else "No Device"
        return f"SIM Balance for {self.phone_number} ({device_info}) - {self.balance}"

