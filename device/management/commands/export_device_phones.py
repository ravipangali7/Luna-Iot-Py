"""
Django management command to export all device phone numbers to phonlist.txt
Usage: python manage.py export_device_phones
"""
import os
from django.core.management.base import BaseCommand, CommandError
from device.models.device import Device


class Command(BaseCommand):
    help = 'Export all device phone numbers to phonlist.txt'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Directory to save phonlist.txt file (default: project root)',
        )

    def handle(self, *args, **options):
        output_dir = options.get('output_dir')
        
        if output_dir:
            # Create directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            output_file_path = os.path.join(output_dir, 'phonlist.txt')
        else:
            # Use project root (where manage.py is located)
            output_file_path = 'phonlist.txt'
        
        self.stdout.write(
            self.style.SUCCESS('Starting device phone export process...')
        )
        
        try:
            # Get all device phone numbers, filter out empty/null values
            phone_numbers = Device.objects.exclude(
                phone__isnull=True
            ).exclude(
                phone=''
            ).values_list('phone', flat=True).distinct().order_by('phone')
            
            # Convert to list and filter out any remaining empty strings
            phone_list = [phone.strip() for phone in phone_numbers if phone and phone.strip()]
            
            total_phones = len(phone_list)
            
            if total_phones == 0:
                self.stdout.write(
                    self.style.WARNING('No device phone numbers found!')
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS(f'Found {total_phones} unique device phone number(s)')
            )
            
            # Write phone numbers to phonlist.txt
            self._export_phones_to_file(phone_list, output_file_path)
            
            # Final summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nExport completed successfully!\n'
                    f'Total phone numbers exported: {total_phones}\n'
                    f'File created: {output_file_path}'
                )
            )
                
        except Exception as e:
            raise CommandError(f'Error during export: {str(e)}')

    def _export_phones_to_file(self, phone_list, file_path):
        """Export phone numbers to text file, one per line"""
        self.stdout.write(f'Writing phone numbers to {file_path}...')
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for phone in phone_list:
                    f.write(f'{phone}\n')
            
            self.stdout.write(
                self.style.SUCCESS(f'  ✓ Exported {len(phone_list)} phone numbers to {file_path}')
            )
        except Exception as e:
            raise CommandError(f'Error writing phonlist.txt: {str(e)}')
