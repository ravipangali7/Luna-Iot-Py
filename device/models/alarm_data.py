from django.db import models
from .device import Device
from shared_utils.constants import AlarmType

class AlarmData(models.Model):
    id = models.BigAutoField(primary_key=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='alarm_data', to_field='imei')
    imei = models.CharField(max_length=15)
    latitude = models.DecimalField(max_digits=12, decimal_places=8)
    longitude = models.DecimalField(max_digits=13, decimal_places=8)
    speed = models.IntegerField()
    realTimeGps = models.BooleanField(db_column='real_time_gps')
    course = models.IntegerField()
    satellite = models.IntegerField()
    battery = models.IntegerField()
    signal = models.IntegerField()
    alarm = models.CharField(max_length=20, choices=AlarmType.choices)
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updatedAt = models.DateTimeField(db_column='updated_at')

    class Meta:
        db_table = 'alarm_data'
        indexes = [
            models.Index(fields=['imei', 'createdAt']),
            models.Index(fields=['imei', 'alarm']),
            models.Index(fields=['createdAt']),
            models.Index(fields=['updatedAt']),
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['alarm']),
            models.Index(fields=['speed']),
        ]
    
    def __str__(self):
        return f"AlarmData for {self.imei} - {self.alarm} at {self.latitude}, {self.longitude}"
