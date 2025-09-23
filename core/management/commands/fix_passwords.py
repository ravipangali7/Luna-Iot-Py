from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from core.models import User


class Command(BaseCommand):
    help = 'Fix existing user passwords to use Django hashing'

    def handle(self, *args, **options):
        self.stdout.write('Starting password fix process...')
        
        # Get all users
        users = User.objects.all()
        fixed_count = 0
        
        for user in users:
            try:
                # Check if password is already Django-hashed
                if user.password.startswith('pbkdf2_') or user.password.startswith('bcrypt_'):
                    self.stdout.write(f'User {user.phone} already has Django-hashed password')
                    continue
                
                # If it's a plain text password or bcrypt hash, we need to reset it
                # For now, let's set a default password that users can change
                user.password = make_password('12345678')
                user.save()
                fixed_count += 1
                self.stdout.write(f'Fixed password for user {user.phone}')
                
            except Exception as e:
                self.stdout.write(f'Error fixing password for user {user.phone}: {str(e)}')
        
        self.stdout.write(f'Password fix completed. Fixed {fixed_count} users.')
        self.stdout.write('Note: All fixed users now have password "default123" - they should change it on first login.')