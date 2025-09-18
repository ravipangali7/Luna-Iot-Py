from django.core.management.base import BaseCommand
from core.models.user import User
from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    help = 'Create a test user for authentication testing'

    def handle(self, *args, **options):
        try:
            # Create user with the credentials from the frontend
            user, created = User.objects.get_or_create(
                phone='977',
                defaults={
                    'name': 'Test User',
                    'password': make_password('password123'),
                    'token': '8ea0797599a329ff0e3b446a5879f51b29d4e84820f758915ebd5f707a288a20',
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created user: {user.name} ({user.phone})')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'User already exists: {user.name} ({user.phone})')
                )
                
            self.stdout.write(f'Phone: {user.phone}')
            self.stdout.write(f'Token: {user.token}')
            self.stdout.write(f'Active: {user.is_active}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating user: {e}')
            )
