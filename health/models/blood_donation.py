from django.db import models
from shared_utils.constants import BloodDonationApplyType

class BloodDonation(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    bloodGroup = models.CharField(max_length=10, db_column='blood_group')
    applyType = models.CharField(max_length=20, choices=BloodDonationApplyType.choices, db_column='apply_type')
    status = models.BooleanField(default=False)
    lastDonatedAt = models.DateTimeField(null=True, blank=True, db_column='last_donated_at')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updatedAt = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'blood_donations'
        indexes = [
            models.Index(fields=['applyType']),
            models.Index(fields=['bloodGroup']),
            models.Index(fields=['status']),
            models.Index(fields=['createdAt']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.bloodGroup} ({self.applyType})"
