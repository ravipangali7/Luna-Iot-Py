from django.db import models
from core.models import User
from shared_utils.constants import NotificationType

class Notification(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=NotificationType.choices)
    sentBy = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sentNotifications', db_column='sent_by_id')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')

    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['type', 'createdAt']),
        ]
    
    def __str__(self):
        return self.title

class UserNotification(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userNotifications')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='userNotifications')
    isRead = models.BooleanField(default=False, db_column='is_read')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    
    class Meta:
        unique_together = ['user', 'notification']
        db_table = 'user_notifications'
        indexes = [
            models.Index(fields=['user', 'isRead']),
        ]
    
    def __str__(self):
        return f"{self.user.name} - {self.notification.title}"
