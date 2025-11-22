from django.db import models
from .vehicle import Vehicle


class VehicleEnergyCost(models.Model):
    ENERGY_TYPE_CHOICES = [
        ('fuel', 'Fuel'),
        ('electric', 'Electric'),
    ]

    id = models.BigAutoField(primary_key=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='energy_costs', db_column='vehicle_id')
    title = models.CharField(max_length=255)
    energy_type = models.CharField(max_length=20, choices=ENERGY_TYPE_CHOICES, db_column='energy_type')
    entry_date = models.DateField(db_column='entry_date')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_unit = models.DecimalField(max_digits=10, decimal_places=2, db_column='total_unit', help_text="Total units (liters/kWh)")
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'vehicle_energy_costs'
        indexes = [
            models.Index(fields=['vehicle']),
            models.Index(fields=['entry_date']),
            models.Index(fields=['energy_type']),
        ]
        ordering = ['-entry_date', '-created_at']

    def __str__(self):
        return f"{self.vehicle.name} - {self.title} ({self.energy_type})"

