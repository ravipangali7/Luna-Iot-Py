from django.db import models
from .public_vehicle import PublicVehicle


class PublicVehicleImage(models.Model):
    """Model for Public Vehicle Images"""
    id = models.BigAutoField(primary_key=True)
    public_vehicle = models.ForeignKey(
        PublicVehicle,
        on_delete=models.CASCADE,
        related_name='images',
        help_text="Public vehicle this image belongs to"
    )
    image = models.ImageField(
        upload_to='public_vehicles/images/',
        help_text="Vehicle image"
    )
    title = models.CharField(max_length=255, blank=True, null=True, help_text="Title for the image")
    order = models.IntegerField(default=0, help_text="Order of the image for display")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'public_vehicle_images'
        verbose_name = 'Public Vehicle Image'
        verbose_name_plural = 'Public Vehicle Images'
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['public_vehicle']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"Image {self.order} for {self.public_vehicle}"

