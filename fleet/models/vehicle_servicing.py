from django.db import models
from .vehicle import Vehicle


class VehicleServicing(models.Model):
    id = models.BigAutoField(primary_key=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='servicings', db_column='vehicle_id')
    title = models.CharField(max_length=255)
    odometer = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'vehicle_servicings'
        indexes = [
            models.Index(fields=['vehicle']),
            models.Index(fields=['date']),
        ]
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.vehicle.name} - {self.title} ({self.date})"

