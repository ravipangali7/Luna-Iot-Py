from django.db import models
from .vehicle import Vehicle


class VehicleExpenses(models.Model):
    EXPENSES_TYPE_CHOICES = [
        ('part', 'Part'),
        ('fine', 'Fine'),
    ]

    id = models.BigAutoField(primary_key=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='expenses', db_column='vehicle_id')
    title = models.CharField(max_length=255)
    expenses_type = models.CharField(max_length=20, choices=EXPENSES_TYPE_CHOICES, db_column='expenses_type')
    entry_date = models.DateField(db_column='entry_date')
    part_expire_month = models.IntegerField(blank=True, null=True, db_column='part_expire_month', help_text="Expiry month for parts")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'vehicle_expenses'
        indexes = [
            models.Index(fields=['vehicle']),
            models.Index(fields=['entry_date']),
            models.Index(fields=['expenses_type']),
        ]
        ordering = ['-entry_date', '-created_at']

    def __str__(self):
        return f"{self.vehicle.name} - {self.title} ({self.expenses_type})"

