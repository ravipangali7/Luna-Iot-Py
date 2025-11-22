from django.db import models
from .vehicle import Vehicle


class VehicleDocument(models.Model):
    id = models.BigAutoField(primary_key=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='documents', db_column='vehicle_id')
    title = models.CharField(max_length=255, help_text="Document type (e.g., Blue Book, License, Insurance)")
    last_expire_date = models.DateField(db_column='last_expire_date')
    expire_in_month = models.IntegerField(db_column='expire_in_month', help_text="Expiry period in months")
    document_image_one = models.ImageField(upload_to='vehicles/documents/', blank=True, null=True, db_column='document_image_one')
    document_image_two = models.ImageField(upload_to='vehicles/documents/', blank=True, null=True, db_column='document_image_two')
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'vehicle_documents'
        indexes = [
            models.Index(fields=['vehicle']),
            models.Index(fields=['last_expire_date']),
            models.Index(fields=['title']),
        ]
        ordering = ['-last_expire_date', '-created_at']

    def __str__(self):
        return f"{self.vehicle.name} - {self.title}"

