from django.db import models


class ExternalAppLink(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    link = models.URLField(blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    logo = models.ImageField(upload_to='external_app_logos/', blank=True, null=True)
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updatedAt = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'external_app_links'
        verbose_name = 'External App Link'
        verbose_name_plural = 'External App Links'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.link}"

