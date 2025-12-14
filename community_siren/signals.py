"""
Django signals for community siren
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CommunitySirenHistory
from .services.community_siren_sms_service import process_community_siren_sms_notifications

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CommunitySirenHistory)
def send_community_siren_notification(sender, instance, created, **kwargs):
    """
    Send SMS notification when a new community siren history is created
    
    Args:
        sender: The model class (CommunitySirenHistory)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    try:
        # Handle new history creation
        if created and instance.source in ['app', 'switch']:
            logger.info(f"New community siren history created: {instance.id} from source: {instance.source}")
            
            # Send SMS notifications to contacts
            sms_result = process_community_siren_sms_notifications(instance)
            
            if sms_result['success']:
                logger.info(f"SMS notifications processed successfully for community siren history {instance.id}")
            else:
                logger.warning(f"Failed to process SMS notifications for community siren history {instance.id}: {sms_result['message']}")
        else:
            logger.debug(f"Community siren history {instance.id} not eligible for notification (created: {created}, source: {instance.source})")
            
    except Exception as e:
        logger.error(f"Error in community siren notification signal for history {instance.id}: {e}")

