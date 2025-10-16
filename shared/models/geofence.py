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

class GeofenceEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('Entry', 'Entry'),
        ('Exit', 'Exit'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    vehicle_id = models.IntegerField(db_column='vehicle_id', help_text='Vehicle ID from vehicles table')
    geofence_id = models.IntegerField(db_column='geofence_id', help_text='Geofence ID from geofences table')
    is_inside = models.BooleanField(default=False, db_column='is_inside', help_text='Current state: True if inside, False if outside')
    last_event_type = models.CharField(max_length=10, choices=EVENT_TYPE_CHOICES, db_column='last_event_type', help_text='Last event type: Entry or Exit')
    last_event_at = models.DateTimeField(db_column='last_event_at', help_text='Timestamp of last event')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updatedAt = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        unique_together = ['vehicle_id', 'geofence_id']
        db_table = 'geofence_events'
        indexes = [
            models.Index(fields=['vehicle_id', 'geofence_id']),
            models.Index(fields=['last_event_at']),
        ]
    
    def __str__(self):
        return f"Vehicle {self.vehicle_id} - Geofence {self.geofence_id} - {self.last_event_type}"