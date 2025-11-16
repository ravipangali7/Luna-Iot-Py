"""
Django management command to export users who have at least one main vehicle
Usage: python manage.py export_main_vehicle_users
"""
import csv
import os
from django.core.management.base import BaseCommand, CommandError
from core.models import User


class Command(BaseCommand):
    help = 'Export users with at least one main vehicle to CSV files (users.csv and phone.csv)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Directory to save CSV files (default: project root)',
        )

    def handle(self, *args, **options):
        output_dir = options.get('output_dir')
        
        if output_dir:
            # Create directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            users_csv_path = os.path.join(output_dir, 'users.csv')
            phone_csv_path = os.path.join(output_dir, 'phone.csv')
        else:
            # Use project root (where manage.py is located)
            users_csv_path = 'users.csv'
            phone_csv_path = 'phone.csv'
        
        self.stdout.write(
            self.style.SUCCESS('Starting user export process...')
        )
        
        try:
            # Query users who have at least one main vehicle
            # Using the related_name 'userVehicles' from UserVehicle model
            users_with_main_vehicles = User.objects.filter(
                userVehicles__isMain=True
            ).distinct().order_by('id')
            
            total_users = users_with_main_vehicles.count()
            
            if total_users == 0:
                self.stdout.write(
                    self.style.WARNING('No users found with main vehicles!')
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS(f'Found {total_users} users with main vehicles')
            )
            
            # Export to users.csv (name, phone)
            self._export_users_csv(users_with_main_vehicles, users_csv_path)
            
            # Export to phone.csv (phone only)
            self._export_phone_csv(users_with_main_vehicles, phone_csv_path)
            
            # Final summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nExport completed successfully!\n'
                    f'Total users exported: {total_users}\n'
                    f'Files created:\n'
                    f'  - {users_csv_path}\n'
                    f'  - {phone_csv_path}'
                )
            )
                
        except Exception as e:
            raise CommandError(f'Error during export: {str(e)}')

    def _export_users_csv(self, users, file_path):
        """Export users to CSV with name and phone columns"""
        self.stdout.write(f'Exporting to {file_path}...')
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(['name', 'phone'])
                
                # Write user data
                exported_count = 0
                for user in users:
                    # Handle None name - use empty string or phone as fallback
                    name = user.name if user.name else ''
                    phone = user.phone if user.phone else ''
                    
                    writer.writerow([name, phone])
                    exported_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Exported {exported_count} users to {file_path}')
                )
        except Exception as e:
            raise CommandError(f'Error writing users.csv: {str(e)}')

    def _export_phone_csv(self, users, file_path):
        """Export phone numbers only to CSV"""
        self.stdout.write(f'Exporting to {file_path}...')
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(['phone'])
                
                # Write phone numbers
                exported_count = 0
                for user in users:
                    phone = user.phone if user.phone else ''
                    writer.writerow([phone])
                    exported_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Exported {exported_count} phone numbers to {file_path}')
                )
        except Exception as e:
            raise CommandError(f'Error writing phone.csv: {str(e)}')

