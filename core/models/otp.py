from django.db import models
from django.utils import timezone
from datetime import timedelta
from shared_utils.constants import OTP_EXPIRY_HOURS

class Otp(models.Model):
    id = models.BigAutoField(primary_key=True)
    phone = models.CharField(max_length=100)
    otp = models.CharField(max_length=6)
    expiresAt = models.DateTimeField(db_column='expires_at')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')

    class Meta:
        db_table = 'otps'
        indexes = [
            models.Index(fields=['phone']),
        ]
    
    def __str__(self):
        return f"OTP for {self.phone}"
    
    def save(self, *args, **kwargs):
        if not self.expiresAt:
            self.expiresAt = timezone.now() + timedelta(hours=OTP_EXPIRY_HOURS)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expiresAt
