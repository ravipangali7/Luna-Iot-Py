from celery.schedules import crontab
from celery import shared_task
from fleet.tasks import cleanup_expired_share_tracks

# Celery Beat periodic task configuration
CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-share-tracks': {
        'task': 'fleet.tasks.cleanup_expired_share_tracks',
        'schedule': crontab(minute='*/10'),  # Run every 10 minutes
    },
}

# Alternative: Using interval instead of crontab
# CELERY_BEAT_SCHEDULE = {
#     'cleanup-expired-share-tracks': {
#         'task': 'fleet.tasks.cleanup_expired_share_tracks',
#         'schedule': 600.0,  # Run every 600 seconds (10 minutes)
#     },
# }
