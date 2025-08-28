from django.core.management.base import BaseCommand
from app.models import *
import bcrypt

class Command(BaseCommand):
    help = 'Seed initial data for the application'

    def handle(self, *args, **options):
        # Create roles
        super_admin_role, _ = Role.objects.get_or_create(
            name='Super Admin',
            defaults={'description': 'Full system access with all permissions'}
        )
        
        dealer_role, _ = Role.objects.get_or_create(
            name='Dealer',
            defaults={'description': 'Dealer access with most permissions'}
        )
        
        customer_role, _ = Role.objects.get_or_create(
            name='Customer',
            defaults={'description': 'Read-only access'}
        )
        
        # Create super admin user
        if not User.objects.filter(phone='977').exists():
            hashed_password = bcrypt.hashpw('nepal'.encode('utf-8'), bcrypt.gensalt(12))
            User.objects.create(
                username='977',
                name='Super Admin',
                phone='977',
                password=hashed_password.decode('utf-8'),
                role=super_admin_role,
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS('Super Admin user created'))
        
        self.stdout.write(self.style.SUCCESS('Data seeding completed'))