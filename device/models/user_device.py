from django.db import models
from core.models import User
from .device import Device

class UserDevice(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userDevices')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='userDevices')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    
    class Meta:
        unique_together = ['user', 'device']
        db_table = 'user_devices'
    
    def __str__(self):
        return f"{self.user.name} - Device {self.device.imei}"
