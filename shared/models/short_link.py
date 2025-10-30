from django.db import models


class ShortLink(models.Model):
    code = models.CharField(max_length=16, unique=True)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    expire_at = models.DateTimeField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.code} -> {self.url}"


