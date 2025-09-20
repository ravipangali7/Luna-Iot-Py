from django.db import models

class Popup(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    image = models.ImageField(upload_to='popup', null=True, blank=True)
    isActive = models.BooleanField(default=True, db_column='is_active')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updatedAt = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'popups'
    
    def __str__(self):
        return self.title
