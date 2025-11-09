from django.db import models
from .luna_tag import LunaTag


class LunaTagData(models.Model):
    id = models.BigAutoField(primary_key=True)
    publicKey = models.ForeignKey(
        LunaTag,
        on_delete=models.CASCADE,
        related_name='lunaTagData',
        db_column='public_key',
        to_field='publicKey'
    )
    battery = models.CharField(max_length=10, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'luna_tag_data'
        indexes = [
            models.Index(fields=['publicKey']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"LunaTagData {self.publicKey.publicKey} - {self.created_at}"

