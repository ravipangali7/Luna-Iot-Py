from django.db import models

class Banner(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='banner', null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    isActive = models.BooleanField(default=True, db_column='is_active')
    click = models.IntegerField(default=0)
    orderPosition = models.IntegerField(default=0, db_column='order_position')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updatedAt = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'banners'
        ordering = ['orderPosition', '-createdAt']
    
    def __str__(self):
        return self.title

