from django.db import models
from .device import Device

class Location(models.Model):
    id = models.BigAutoField(primary_key=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='locations', to_field='imei')
    imei = models.CharField(max_length=15)
    latitude = models.DecimalField(max_digits=12, decimal_places=8)
    longitude = models.DecimalField(max_digits=13, decimal_places=8)
    speed = models.IntegerField()
    course = models.IntegerField()
    realTimeGps = models.BooleanField(db_column='real_time_gps')
    satellite = models.IntegerField()
    createdAt = models.DateTimeField(db_column='created_at')
    updatedAt = models.DateTimeField(db_column='updated_at')

    class Meta:
        db_table = 'locations'
        indexes = [
            models.Index(fields=['imei', 'createdAt']),
            models.Index(fields=['createdAt']),
            models.Index(fields=['updatedAt']),
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['speed']),
        ]
    
    def __str__(self):
        return f"Location for {self.imei} at {self.latitude}, {self.longitude}"