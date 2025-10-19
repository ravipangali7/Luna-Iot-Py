"""
Django signals for alert system
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AlertHistory
from .services.alert_notification_service import send_alert_notification_via_nodejs

logger = logging.getLogger(__name__)


@receiver(post_save, sender=AlertHistory)
def send_alert_notification(sender, instance, created, **kwargs):
    """
    Send real-time notification when a new alert is created
    
    Args:
        sender: The model class (AlertHistory)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    try:
        # Only send notification for new alerts from app or geofence sources
        if created and instance.source in ['app', 'geofence']:
            logger.info(f"New alert created: {instance.id} from source: {instance.source}")
            
            # Send notification via Node.js
            success = send_alert_notification_via_nodejs(instance)
            
            if success:
                logger.info(f"Alert notification sent successfully for alert {instance.id}")
            else:
                logger.warning(f"Failed to send alert notification for alert {instance.id}")
        else:
            logger.debug(f"Alert {instance.id} not eligible for notification (created: {created}, source: {instance.source})")
            
    except Exception as e:
        logger.error(f"Error in alert notification signal for alert {instance.id}: {e}")
