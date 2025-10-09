from django.utils import timezone
from django.db import transaction
from fleet.models.share_track import ShareTrack
import logging

logger = logging.getLogger(__name__)


class ShareTrackCleanupService:
    """
    Service class for cleaning up expired share tracks
    """
    
    @staticmethod
    def cleanup_expired_tracks(dry_run=False):
        """
        Clean up expired share tracks from the database
        
        Args:
            dry_run (bool): If True, only count expired tracks without deleting them
            
        Returns:
            dict: Result containing status, count, and details
        """
        try:
            now = timezone.now()
            
            # Find expired share tracks
            expired_tracks = ShareTrack.objects.filter(scheduled_for__lt=now)
            count = expired_tracks.count()
            
            if count == 0:
                return {
                    'status': 'success',
                    'deleted_count': 0,
                    'message': 'No expired share tracks found',
                    'timestamp': now.isoformat()
                }
            
            if dry_run:
                # Return details without deleting
                track_details = []
                for track in expired_tracks:
                    track_details.append({
                        'id': str(track.id),
                        'imei': track.imei,
                        'token': track.token,
                        'created_at': track.created_at.isoformat(),
                        'scheduled_for': track.scheduled_for.isoformat(),
                        'expired_minutes_ago': int((now - track.scheduled_for).total_seconds() / 60)
                    })
                
                return {
                    'status': 'dry_run',
                    'would_delete_count': count,
                    'track_details': track_details,
                    'timestamp': now.isoformat()
                }
            
            # Delete expired tracks
            with transaction.atomic():
                deleted_count, _ = expired_tracks.delete()
                
                logger.info(f'Cleaned up {deleted_count} expired share tracks')
                
                return {
                    'status': 'success',
                    'deleted_count': deleted_count,
                    'message': f'Successfully deleted {deleted_count} expired share tracks',
                    'timestamp': now.isoformat()
                }
                
        except Exception as e:
            logger.error(f'Error in ShareTrackCleanupService.cleanup_expired_tracks: {e}')
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    @staticmethod
    def get_expired_tracks_count():
        """
        Get the count of expired share tracks without deleting them
        
        Returns:
            int: Number of expired share tracks
        """
        now = timezone.now()
        return ShareTrack.objects.filter(scheduled_for__lt=now).count()
    
    @staticmethod
    def get_active_tracks_count():
        """
        Get the count of active (non-expired) share tracks
        
        Returns:
            int: Number of active share tracks
        """
        now = timezone.now()
        return ShareTrack.objects.filter(scheduled_for__gte=now).count()
    
    @staticmethod
    def get_all_tracks_stats():
        """
        Get comprehensive statistics about share tracks
        
        Returns:
            dict: Statistics about share tracks
        """
        now = timezone.now()
        
        total_tracks = ShareTrack.objects.count()
        active_tracks = ShareTrack.objects.filter(scheduled_for__gte=now).count()
        expired_tracks = ShareTrack.objects.filter(scheduled_for__lt=now).count()
        
        return {
            'total_tracks': total_tracks,
            'active_tracks': active_tracks,
            'expired_tracks': expired_tracks,
            'timestamp': now.isoformat()
        }
