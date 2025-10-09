from celery import shared_task
from django.utils import timezone
from django.db import transaction
from fleet.models.share_track import ShareTrack
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_share_tracks():
    """
    Celery task to clean up expired share tracks.
    This task should be scheduled to run every 10 minutes.
    """
    try:
        now = timezone.now()
        
        # Find expired share tracks
        expired_tracks = ShareTrack.objects.filter(scheduled_for__lt=now)
        count = expired_tracks.count()
        
        if count == 0:
            logger.info('No expired share tracks found for cleanup')
            return {'status': 'success', 'deleted_count': 0}
        
        with transaction.atomic():
            # Delete expired tracks
            deleted_count, _ = expired_tracks.delete()
            
            logger.info(f'Cleaned up {deleted_count} expired share tracks')
            
            return {
                'status': 'success',
                'deleted_count': deleted_count,
                'timestamp': now.isoformat()
            }
            
    except Exception as e:
        logger.error(f'Error in cleanup_expired_share_tracks task: {e}')
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def cleanup_expired_share_tracks_with_notification():
    """
    Celery task to clean up expired share tracks with detailed logging.
    This version provides more detailed information about the cleanup process.
    """
    try:
        now = timezone.now()
        
        # Find expired share tracks
        expired_tracks = ShareTrack.objects.filter(scheduled_for__lt=now)
        count = expired_tracks.count()
        
        if count == 0:
            logger.info('No expired share tracks found for cleanup')
            return {'status': 'success', 'deleted_count': 0, 'message': 'No expired tracks found'}
        
        # Log details about expired tracks before deletion
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
        
        with transaction.atomic():
            # Delete expired tracks
            deleted_count, _ = expired_tracks.delete()
            
            logger.info(f'Cleaned up {deleted_count} expired share tracks')
            logger.debug(f'Deleted tracks details: {track_details}')
            
            return {
                'status': 'success',
                'deleted_count': deleted_count,
                'track_details': track_details,
                'timestamp': now.isoformat()
            }
            
    except Exception as e:
        logger.error(f'Error in cleanup_expired_share_tracks_with_notification task: {e}')
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }
