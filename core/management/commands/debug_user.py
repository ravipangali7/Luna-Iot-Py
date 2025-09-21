from django.core.management.base import BaseCommand
from core.models.user import User
from django.contrib.auth.hashers import make_password, check_password


class Command(BaseCommand):
    help = 'Update all user passwords to "nepal" using Django hashing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually updating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        try:
            # Get all users
            users = User.objects.all()
            updated_count = 0
            
            self.stdout.write(f'Found {users.count()} users in database')
            
            for user in users:
                self.stdout.write(f'\nProcessing user: {user.name} ({user.phone})')
                self.stdout.write(f'Current password hash: {user.password[:50]}...')
                
                # Test current password with "nepal"
                is_nepal = check_password('nepal', user.password)
                self.stdout.write(f'Current password is "nepal": {is_nepal}')
                
                if not is_nepal:
                    if not dry_run:
                        # Update password to "nepal" using Django hashing
                        user.password = make_password('nepal')
                        user.save()
                        updated_count += 1
                        self.stdout.write(self.style.SUCCESS(f'Updated password for {user.phone}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Would update password for {user.phone}'))
                else:
                    self.stdout.write(f'Password already correct for {user.phone}')
            
            if not dry_run:
                self.stdout.write(self.style.SUCCESS(f'\nPassword update completed. Updated {updated_count} users.'))
                self.stdout.write('All users now have password "nepal"')
            else:
                self.stdout.write(self.style.WARNING(f'\nDry run completed. Would update {updated_count} users.'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            import traceback
            traceback.print_exc()