from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from fleet.models.share_track import ShareTrack
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up expired share tracks from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        now = timezone.now()
        
        # Find expired share tracks
        expired_tracks = ShareTrack.objects.filter(scheduled_for__lt=now)
        count = expired_tracks.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No expired share tracks found.')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} expired share track(s)'
                )
            )
            if verbose:
                for track in expired_tracks:
                    self.stdout.write(
                        f'  - IMEI: {track.imei}, '
                        f'Token: {track.token}, '
                        f'Expired: {track.scheduled_for}'
                    )
        else:
            try:
                with transaction.atomic():
                    # Delete expired tracks
                    deleted_count, _ = expired_tracks.delete()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully deleted {deleted_count} expired share track(s)'
                        )
                    )
                    
                    if verbose:
                        self.stdout.write('Deleted tracks:')
                        for track in expired_tracks:
                            self.stdout.write(
                                f'  - IMEI: {track.imei}, '
                                f'Token: {track.token}, '
                                f'Expired: {track.scheduled_for}'
                            )
                            
                logger.info(f'Cleaned up {deleted_count} expired share tracks')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error deleting expired share tracks: {e}')
                )
                logger.error(f'Error in cleanup_expired_share_tracks: {e}')
                raise