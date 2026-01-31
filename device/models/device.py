from django.db import models
from shared_utils.constants import SimType, ProtocolType, DeviceModelType, DeviceType

class Device(models.Model):
    id = models.BigAutoField(primary_key=True)
    imei = models.CharField(max_length=15, unique=True)
    phone = models.CharField(max_length=20)
    serial_number = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    sim = models.CharField(max_length=10, choices=SimType.choices)
    protocol = models.CharField(max_length=20, choices=ProtocolType.choices, default=ProtocolType.GT06)
    iccid = models.CharField(max_length=255, null=True, blank=True, default="")
    model = models.CharField(max_length=10, choices=DeviceModelType.choices)
    type = models.CharField(max_length=10, choices=DeviceType.choices, default=DeviceType.GPS, null=True, blank=True)
    subscription_plan = models.ForeignKey('SubscriptionPlan', on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updatedAt = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'devices'
        indexes = [
            models.Index(fields=['imei']),
            models.Index(fields=['phone']),
            models.Index(fields=['serial_number']),
        ]
    
    def __str__(self):
        return f"Device {self.imei} ({self.model})"