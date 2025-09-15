from django.db import models
from shared.models import Geofence
from .vehicle import Vehicle

class GeofenceVehicle(models.Model):
    id = models.BigAutoField(primary_key=True)
    geofence = models.ForeignKey(Geofence, on_delete=models.CASCADE, related_name='vehicles')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='geofences')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    
    class Meta:
        unique_together = ['geofence', 'vehicle']
        db_table = 'geofence_vehicles'
    
    def __str__(self):
        return f"{self.geofence.title} - {self.vehicle.name}"
