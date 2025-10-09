from django.db import models
from core.models import User
from .vehicle import Vehicle

class UserVehicle(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userVehicles')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='userVehicles')
    isMain = models.BooleanField(default=False, db_column='is_main')
    
    # Vehicle-specific permissions
    allAccess = models.BooleanField(default=False, db_column='all_access')
    liveTracking = models.BooleanField(default=False, db_column='live_tracking')
    history = models.BooleanField(default=False)
    report = models.BooleanField(default=False)
    vehicleProfile = models.BooleanField(default=False, db_column='vehicle_profile')
    events = models.BooleanField(default=False)
    geofence = models.BooleanField(default=False)
    edit = models.BooleanField(default=False)
    shareTracking = models.BooleanField(default=False, db_column='share_tracking')
    notification = models.BooleanField(default=True)
    # Engine relay permission for this user on this vehicle
    relay = models.BooleanField(default=False)
    
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    
    class Meta:
        unique_together = ['user', 'vehicle']
        db_table = 'user_vehicles'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['vehicle']),
            models.Index(fields=['user', 'isMain']),
        ]
    
    def __str__(self):
        return f"{self.user.name} - {self.vehicle.name}"