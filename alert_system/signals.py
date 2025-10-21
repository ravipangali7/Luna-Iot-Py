"""
Django signals for alert system
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import AlertHistory
from .services.alert_notification_service import send_alert_notification_via_nodejs
from .services.alert_sms_service import process_alert_sms_notifications, send_alert_acceptance_sms

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=AlertHistory)
def track_alert_changes(sender, instance, **kwargs):
    """
    Track changes to status and remarks fields before saving
    """
    try:
        if instance.pk:
            # Get the old instance from database
            old_instance = AlertHistory.objects.get(pk=instance.pk)
            
            # Store old values for comparison
            instance._old_status = old_instance.status
            instance._old_remarks = old_instance.remarks
        else:
            # New instance
            instance._old_status = None
            instance._old_remarks = None
            
    except AlertHistory.DoesNotExist:
        # Instance doesn't exist yet (new)
        instance._old_status = None
        instance._old_remarks = None
    except Exception as e:
        logger.error(f"Error tracking alert changes for alert {instance.id}: {e}")
        instance._old_status = None
        instance._old_remarks = None


@receiver(post_save, sender=AlertHistory)
def send_alert_notification(sender, instance, created, **kwargs):
    """
    Send real-time notification when a new alert is created or updated
    
    Args:
        sender: The model class (AlertHistory)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    try:
        # Handle new alert creation
        if created and instance.source in ['app', 'geofence', 'switch']:
            logger.info(f"New alert created: {instance.id} from source: {instance.source}")
            
            # Send notification via Node.js (existing functionality)
            success = send_alert_notification_via_nodejs(instance)
            
            if success:
                logger.info(f"Alert notification sent successfully for alert {instance.id}")
            else:
                logger.warning(f"Failed to send alert notification for alert {instance.id}")
            
            # Send SMS notifications to contacts and activate buzzers
            sms_result = process_alert_sms_notifications(instance)
            
            if sms_result['success']:
                logger.info(f"SMS notifications processed successfully for alert {instance.id}")
            else:
                logger.warning(f"Failed to process SMS notifications for alert {instance.id}: {sms_result['message']}")
                
        # Handle status or remarks updates
        elif not created and hasattr(instance, '_old_status') and hasattr(instance, '_old_remarks'):
            status_changed = instance._old_status != instance.status
            remarks_changed = instance._old_remarks != instance.remarks
            
            if status_changed or remarks_changed:
                logger.info(f"Alert {instance.id} updated - Status changed: {status_changed}, Remarks changed: {remarks_changed}")
                
                # Send acceptance SMS to alert sender
                acceptance_result = send_alert_acceptance_sms(instance)
                
                if acceptance_result['success']:
                    logger.info(f"Acceptance SMS sent successfully for alert {instance.id}")
                else:
                    logger.warning(f"Failed to send acceptance SMS for alert {instance.id}: {acceptance_result['message']}")
        else:
            logger.debug(f"Alert {instance.id} not eligible for notification (created: {created}, source: {instance.source})")
            
    except Exception as e:
        logger.error(f"Error in alert notification signal for alert {instance.id}: {e}")
