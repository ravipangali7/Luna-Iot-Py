from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from device.models.luna_tag import LunaTag
from device.models.user_luna_tag import UserLunaTag
from device.models.luna_tag_data import LunaTagData
from device.services.luna_tag_api_service import fetch_tag_data
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch Luna Tag data from external API for all active tags'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        # Get all active LunaTags (those with active UserLunaTag)
        active_user_tags = UserLunaTag.objects.filter(is_active=True).select_related('publicKey')
        
        # Get unique publicKeys
        active_public_keys = set()
        for user_tag in active_user_tags:
            active_public_keys.add(user_tag.publicKey.publicKey)
        
        if not active_public_keys:
            self.stdout.write(
                self.style.WARNING('No active Luna Tags found.')
            )
            return
        
        self.stdout.write(
            f'Found {len(active_public_keys)} active Luna Tag(s) to fetch data for.'
        )
        
        success_count = 0
        error_count = 0
        
        for public_key in active_public_keys:
            try:
                # Fetch data from API
                tag_data = fetch_tag_data(public_key)
                
                if not tag_data:
                    error_count += 1
                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  - Failed to fetch data for publicKey: {public_key}'
                            )
                        )
                    continue
                
                # Get or create LunaTag
                try:
                    luna_tag = LunaTag.objects.get(publicKey=public_key)
                except LunaTag.DoesNotExist:
                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  - LunaTag not found for publicKey: {public_key}, skipping'
                            )
                        )
                    error_count += 1
                    continue
                
                # Save data to LunaTagData
                with transaction.atomic():
                    LunaTagData.objects.create(
                        publicKey=luna_tag,
                        battery=tag_data.get('battery', ''),
                        latitude=tag_data.get('latitude'),
                        longitude=tag_data.get('longitude'),
                    )
                    
                    success_count += 1
                    if verbose:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  - Successfully saved data for publicKey: {public_key}'
                            )
                        )
                        self.stdout.write(
                            f'     Battery: {tag_data.get("battery", "N/A")}, '
                            f'Lat: {tag_data.get("latitude", "N/A")}, '
                            f'Lon: {tag_data.get("longitude", "N/A")}'
                        )
                
            except Exception as e:
                error_count += 1
                logger.error(f'Error processing publicKey {public_key}: {e}')
                if verbose:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  - Error processing publicKey {public_key}: {e}'
                        )
                    )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted: {success_count} successful, {error_count} failed'
            )
        )
        
        logger.info(
            f'Fetched Luna Tag data: {success_count} successful, {error_count} failed'
        )

