from django.db import models
from shared.models.sim_balance import SimBalance


class ResourceType(models.TextChoices):
    DATA = 'DATA', 'Data'
    SMS = 'SMS', 'SMS'
    VOICE = 'VOICE', 'Voice'


class SimFreeResource(models.Model):
    """Model to store free resources (DATA, SMS, VOICE) for SIM balances"""
    id = models.BigAutoField(primary_key=True)
    sim_balance = models.ForeignKey(
        SimBalance, 
        on_delete=models.CASCADE, 
        related_name='free_resources',
        help_text="Associated SIM balance"
    )
    name = models.CharField(max_length=255, help_text="Resource name (e.g., 'm2m 50mb', '15 Pcs')")
    resource_type = models.CharField(
        max_length=20, 
        choices=ResourceType.choices,
        help_text="Type of resource (DATA, SMS, VOICE)"
    )
    remaining = models.CharField(max_length=100, help_text="Remaining amount (e.g., '49.83MB', '15 Pcs', '40 Min')")
    expiry = models.DateTimeField(help_text="Resource expiry date")
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')

    class Meta:
        db_table = 'sim_free_resources'
        verbose_name = 'SIM Free Resource'
        verbose_name_plural = 'SIM Free Resources'
        indexes = [
            models.Index(fields=['sim_balance', 'resource_type']),
            models.Index(fields=['expiry']),
        ]
        unique_together = [['sim_balance', 'name', 'expiry']]  # Prevent duplicates
    
    def __str__(self):
        return f"{self.name} ({self.resource_type}) - {self.remaining} until {self.expiry}"

