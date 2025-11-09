from django.db import models
from .luna_tag import LunaTag


class UserLunaTag(models.Model):
    id = models.BigAutoField(primary_key=True)
    publicKey = models.ForeignKey(
        LunaTag,
        on_delete=models.CASCADE,
        related_name='userLunaTags',
        db_column='public_key',
        to_field='publicKey'
    )
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='uploads/luna_tags/', blank=True, null=True)
    expire_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_luna_tags'
        indexes = [
            models.Index(fields=['publicKey']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} - {self.publicKey.publicKey}"

