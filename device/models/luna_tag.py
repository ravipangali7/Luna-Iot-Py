from django.db import models


class LunaTag(models.Model):
    id = models.BigAutoField(primary_key=True)
    publicKey = models.CharField(max_length=255, unique=True, db_column='public_key')
    is_lost_mode = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'luna_tags'
        indexes = [
            models.Index(fields=['publicKey']),
        ]

    def __str__(self):
        return f"LunaTag {self.publicKey}"

