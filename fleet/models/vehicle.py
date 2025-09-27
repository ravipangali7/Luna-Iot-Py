from django.db import models
from device.models import Device
from shared_utils.constants import VehicleType

class Vehicle(models.Model):
    id = models.BigAutoField(primary_key=True)
    imei = models.CharField(max_length=15, unique=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='vehicles', to_field='imei')
    name = models.CharField(max_length=255)
    vehicleNo = models.CharField(max_length=255, db_column='vehicle_no')
    vehicleType = models.CharField(max_length=20, choices=VehicleType.choices, default=VehicleType.CAR, db_column='vehicle_type')
    odometer = models.DecimalField(max_digits=10, decimal_places=2)
    mileage = models.DecimalField(max_digits=10, decimal_places=2)
    minimumFuel = models.DecimalField(max_digits=10, decimal_places=2, db_column='minimum_fuel')
    speedLimit = models.IntegerField(default=60, db_column='speed_limit')
    expireDate = models.DateTimeField(null=True, blank=True, db_column='expire_date')
    is_active = models.BooleanField(default=True, db_column='is_active')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updatedAt = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'vehicles'
        indexes = [
            models.Index(fields=['imei']),
            models.Index(fields=['vehicleType']),
            models.Index(fields=['createdAt']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.vehicleNo})"
