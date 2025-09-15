from django.db import models
from core.models import User
from shared_utils.constants import GeofenceType

class Geofence(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=GeofenceType.choices)
    boundary = models.JSONField()
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updatedAt = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'geofences'
    
    def __str__(self):
        return self.title

class GeofenceUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    geofence = models.ForeignKey(Geofence, on_delete=models.CASCADE, related_name='users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='geofences')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    
    class Meta:
        unique_together = ['geofence', 'user']
        db_table = 'geofence_users'
    
    def __str__(self):
        return f"{self.geofence.title} - {self.user.name}"