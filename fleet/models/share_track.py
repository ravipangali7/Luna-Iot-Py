from django.db import models
from core.models import User
from django.utils import timezone
import uuid


class ShareTrack(models.Model):
    id = models.AutoField(primary_key=True)
    imei = models.CharField(max_length=20, help_text="Vehicle IMEI number")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="User who created the share")
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(help_text="When this share will expire")
    is_active = models.BooleanField(default=True, help_text="Whether this share is still active")
    
    class Meta:
        db_table = 'share_track'
        verbose_name = 'Share Track'
        verbose_name_plural = 'Share Tracks'
        indexes = [
            models.Index(fields=['imei']),
            models.Index(fields=['token']),
            models.Index(fields=['scheduled_for']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"Share Track for {self.imei} - {self.token}"
    
    @property
    def is_expired(self):
        """Check if the share has expired"""
        return timezone.now() > self.scheduled_for
    
    def deactivate(self):
        """Deactivate the share"""
        self.is_active = False
        self.save(update_fields=['is_active'])
