"""
Django Signals for Notification System
Handles automatic push notification sending when notifications are created
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
import logging

from .models import Notification, UserNotification
from api_common.services.nodejs_notification_service import send_push_notification_to_user_notifications, send_push_notification_to_specific_user

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notification)
def send_notification_push(sender, instance, created, **kwargs):
    """
    Send push notification when a new notification is created
    """
    if created:
        try:
            logger.info(f"Sending push notification via Node.js API for notification {instance.id}")
            
            # Use the Node.js API service to send push notifications
            success = send_push_notification_to_user_notifications(instance)
            
            if success:
                logger.info(f"Successfully sent push notification via Node.js API for notification {instance.id}")
            else:
                logger.warning(f"Failed to send push notification via Node.js API for notification {instance.id}")
                
        except Exception as e:
            logger.error(f"Error sending push notification via Node.js API for notification {instance.id}: {e}")


@receiver(post_save, sender=UserNotification)
def send_individual_notification_push(sender, instance, created, **kwargs):
    """
    Send push notification when a new UserNotification is created
    This ensures notifications are sent even if they're created after the main notification
    """
    if created:
        try:
            logger.info(f"Sending individual push notification via Node.js API for UserNotification {instance.id}")
            
            # Send notification to this specific user via Node.js API
            notification = instance.notification
            user = instance.user
            
            if user.fcm_token and user.is_active:
                success = send_push_notification_to_specific_user(notification, user)
                
                if success:
                    logger.info(f"Successfully sent individual push notification via Node.js API to user {user.id}")
                else:
                    logger.warning(f"Failed to send individual push notification via Node.js API to user {user.id}")
            else:
                logger.warning(f"User {user.id} has no FCM token or is inactive")
                
        except Exception as e:
            logger.error(f"Error sending individual push notification via Node.js API for UserNotification {instance.id}: {e}")