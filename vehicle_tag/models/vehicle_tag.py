from django.db import models
from core.models import User


class VehicleTag(models.Model):
    """Model for Vehicle Tag"""
    
    REGISTER_TYPE_CHOICES = [
        ('traditional_old', 'Traditional Old'),
        ('traditional_new', 'Traditional New'),
        ('embossed', 'Embossed'),
    ]
    
    VEHICLE_CATEGORY_CHOICES = [
        ('private', 'Private'),
        ('public', 'Public'),
        ('government', 'Government'),
        ('diplomats', 'Diplomats'),
        ('non_profit_org', 'Non Profit Organization'),
        ('corporation', 'Corporation'),
        ('tourism', 'Tourism'),
        ('ministry', 'Ministry'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='vehicle_tags',
        null=True,
        blank=True,
        help_text="User who owns this vehicle tag"
    )
    vtid = models.CharField(
        max_length=50,
        unique=True,
        db_column='vtid',
        help_text="Vehicle Tag ID in format VTID{id}"
    )
    vehicle_model = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_column='vehicle_model',
        help_text="Model of the vehicle"
    )
    registration_no = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_column='registration_no',
        help_text="Vehicle registration number"
    )
    register_type = models.CharField(
        max_length=50,
        choices=REGISTER_TYPE_CHOICES,
        blank=True,
        null=True,
        db_column='register_type',
        help_text="Type of registration"
    )
    vehicle_category = models.CharField(
        max_length=50,
        choices=VEHICLE_CATEGORY_CHOICES,
        blank=True,
        null=True,
        db_column='vehicle_category',
        help_text="Category of the vehicle"
    )
    sos_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_column='sos_number',
        help_text="SOS contact number"
    )
    sms_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_column='sms_number',
        help_text="SMS contact number"
    )
    is_active = models.BooleanField(
        default=True,
        db_column='is_active',
        help_text="Whether the tag is active"
    )
    is_downloaded = models.BooleanField(
        default=False,
        db_column='is_downloaded',
        help_text="Whether the tag has been downloaded"
    )
    visit_count = models.IntegerField(
        default=0,
        db_column='visit_count',
        help_text="Number of times the vehicle tag has been accessed/viewed"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'vehicle_tags'
        verbose_name = 'Vehicle Tag'
        verbose_name_plural = 'Vehicle Tags'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vtid']),
            models.Index(fields=['user']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate vtid if not set
        if not self.vtid:
            # If this is a new object (no id yet), save first to get id from database
            if not self.id:
                # Save without vtid first to get auto-generated id
                # Remove update_fields from kwargs if present to allow full save
                update_fields = kwargs.pop('update_fields', None)
                super().save(*args, **kwargs)
                # Now set vtid based on the auto-generated id
                self.vtid = f"VTID{self.id}"
                # Update only vtid field
                super().save(update_fields=['vtid'])
            else:
                # Object already has id, just set vtid and save
                self.vtid = f"VTID{self.id}"
                super().save(*args, **kwargs)
        else:
            # vtid already set, just save normally
            super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.vtid} - {self.registration_no or 'No Registration'}"

