from django.db import models
from django.core.exceptions import ValidationError
from core.models import User, Institute


class PhoneBook(models.Model):
    """Model for Phone Books - can belong to user or institute"""
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='phone_books',
        null=True,
        blank=True,
        help_text="User who owns this phone book (null if owned by institute)"
    )
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE,
        related_name='phone_books',
        null=True,
        blank=True,
        help_text="Institute that owns this phone book (null if owned by user)"
    )
    name = models.CharField(max_length=255, help_text="Name of the phone book")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'phone_books'
        verbose_name = 'Phone Book'
        verbose_name_plural = 'Phone Books'
        ordering = ['name']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['institute']),
            models.Index(fields=['name']),
        ]
    
    def clean(self):
        """Validate that exactly one of user or institute is provided"""
        if not self.user and not self.institute:
            raise ValidationError("Either user or institute must be provided")
        if self.user and self.institute:
            raise ValidationError("Phone book cannot belong to both user and institute")
    
    def save(self, *args, **kwargs):
        """Override save to call clean validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        owner = self.user.name if self.user else (self.institute.name if self.institute else "Unknown")
        return f"{self.name} ({owner})"


class PhoneBookNumber(models.Model):
    """Model for Phone Book Numbers (contacts within a phone book)"""
    id = models.BigAutoField(primary_key=True)
    phonebook = models.ForeignKey(
        PhoneBook,
        on_delete=models.CASCADE,
        related_name='numbers',
        help_text="Phone book this number belongs to"
    )
    name = models.CharField(max_length=255, help_text="Contact name")
    phone = models.CharField(max_length=20, help_text="Phone number")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'phone_book_numbers'
        verbose_name = 'Phone Book Number'
        verbose_name_plural = 'Phone Book Numbers'
        ordering = ['name']
        indexes = [
            models.Index(fields=['phonebook']),
            models.Index(fields=['phone']),
        ]
        unique_together = [['phonebook', 'phone']]  # Phone must be unique within a phone book
    
    def __str__(self):
        return f"{self.name} ({self.phone})"
