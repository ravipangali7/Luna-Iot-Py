from django.db import models
from django.contrib.auth.models import Permission


class SubscriptionPlan(models.Model):
    """Subscription Plan model"""
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    dealer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    purchasing_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'subscription_plans'
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['price']),
        ]
    
    def __str__(self):
        return f"{self.title} - ${self.price}"


class SubscriptionPlanPermission(models.Model):
    """Subscription Plan Permission relationship model"""
    id = models.BigAutoField(primary_key=True)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='subscription_plan_permissions')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='permissions')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    
    class Meta:
        unique_together = ['permission', 'subscription_plan']
        db_table = 'subscription_plan_permissions'
        indexes = [
            models.Index(fields=['permission', 'subscription_plan']),
            models.Index(fields=['subscription_plan']),
        ]
    
    def __str__(self):
        return f"{self.subscription_plan.title} - {self.permission.name}"
