from django.db import models
from device.models import Device

class Recharge(models.Model):
    id = models.BigAutoField(primary_key=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='recharges')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')

    class Meta:
        db_table = 'recharges'
        indexes = [
            models.Index(fields=['device']),
            models.Index(fields=['createdAt']),
        ]
    
    def __str__(self):
        return f"Recharge {self.amount} for Device {self.device.imei}"
