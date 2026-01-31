"""
Management command to fix user with id=0 in the database.

MySQL/MariaDB AUTO_INCREMENT fields do not accept 0 as a valid value by default.
This command finds any user with id=0 and updates it to a valid auto-increment ID.

Usage:
    python manage.py fix_user_zero_id
    python manage.py fix_user_zero_id --dry-run  # Preview changes without applying
"""
from django.core.management.base import BaseCommand
from django.db import connection
from core.models import User


class Command(BaseCommand):
    help = 'Fix user with id=0 by updating to a valid auto-increment ID'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without actually modifying the database',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        self.stdout.write('Checking for users with id=0...')
        
        # Check if there's a user with id=0
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, phone, name FROM users WHERE id = 0")
                row = cursor.fetchone()
                
                if not row:
                    self.stdout.write(self.style.SUCCESS('No user found with id=0. Database is clean.'))
                    return
                
                user_id, phone, name = row
                self.stdout.write(f'Found user with id=0: phone={phone}, name={name}')
                
                # Get the current max ID
                cursor.execute("SELECT MAX(id) FROM users WHERE id > 0")
                max_id_row = cursor.fetchone()
                max_id = max_id_row[0] if max_id_row[0] else 0
                new_id = max_id + 1
                
                self.stdout.write(f'Current max user ID: {max_id}')
                self.stdout.write(f'New ID for user with id=0: {new_id}')
                
                if dry_run:
                    self.stdout.write(self.style.WARNING(
                        f'\nDRY RUN: Would update user id from 0 to {new_id}'
                    ))
                    self.stdout.write(self.style.WARNING(
                        f'DRY RUN: Would set AUTO_INCREMENT to {new_id + 1}'
                    ))
                    return
                
                # Update the user's ID
                self.stdout.write(f'Updating user id from 0 to {new_id}...')
                cursor.execute("UPDATE users SET id = %s WHERE id = 0", [new_id])
                
                # Reset AUTO_INCREMENT
                self.stdout.write(f'Setting AUTO_INCREMENT to {new_id + 1}...')
                cursor.execute(f"ALTER TABLE users AUTO_INCREMENT = {new_id + 1}")
                
                self.stdout.write(self.style.SUCCESS(
                    f'\nSuccessfully fixed user id: 0 -> {new_id}'
                ))
                self.stdout.write(self.style.SUCCESS(
                    f'User {name} ({phone}) now has id={new_id}'
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fixing user id: {str(e)}'))
            raise
