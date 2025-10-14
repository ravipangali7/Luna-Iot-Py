from django.db import models
from .device import Device

class Status(models.Model):
    id = models.BigAutoField(primary_key=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='statuses', to_field='imei')
    imei = models.CharField(max_length=15)
    battery = models.IntegerField()
    signal = models.IntegerField()
    ignition = models.BooleanField()
    charging = models.BooleanField()
    relay = models.BooleanField()
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updatedAt = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'statuses'
        indexes = [
            models.Index(fields=['imei', 'createdAt']),
            models.Index(fields=['imei', 'ignition']),
            models.Index(fields=['createdAt']),
            models.Index(fields=['updatedAt']),
            models.Index(fields=['battery']),
        ]
    
    def __str__(self):
        return f"Status for {self.imei} - Battery: {self.battery}%, Signal: {self.signal}%"