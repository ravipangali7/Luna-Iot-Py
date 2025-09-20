import firebase_admin
from firebase_admin import credentials, messaging
import os
from luna_iot_py.settings import BASE_DIR
from core.models.user import User
from shared.models import Notification, UserNotification
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
try:
    cred = credentials.Certificate(os.path.join(BASE_DIR, 'firebase-service.json'))
    firebase_admin.initialize_app(cred)
    FIREBASE_INITIALIZED = True
except Exception as e:
    logger.error(f"Firebase initialization failed: {e}")
    FIREBASE_INITIALIZED = False


def send_push_notification(notification_id, title, body, notification_type, target_user_ids=None, target_role_ids=None):
    """
    Send push notification based on notification type
    Args:
        notification_id: ID of the notification
        title: Notification title
        body: Notification body
        notification_type: Type of notification ('all', 'specific', 'role')
        target_user_ids: List of user IDs for 'specific' type
        target_role_ids: List of role IDs for 'role' type
    """
    if not FIREBASE_INITIALIZED:
        logger.error("Firebase not initialized, cannot send notifications")
        return False
    
    try:
        # Get FCM tokens based on notification type
        fcm_tokens = get_fcm_tokens_by_type(notification_type, target_user_ids, target_role_ids)
        
        if not fcm_tokens:
            logger.warning(f"No FCM tokens found for notification type: {notification_type}")
            return False
        
        # Create messages
        messages = []
        for token in fcm_tokens:
            if token:  # Only send to valid tokens
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body,
                    ),
                    data={
                        'notificationId': str(notification_id),
                        'type': notification_type
                    },
                    token=token,
                )
                messages.append(message)
        
        if messages:
            # Send notifications in batches
            response = messaging.send_all(messages)
            logger.info(f"Successfully sent {response.success_count} notifications, {response.failure_count} failed")
            return True
        else:
            logger.warning("No valid messages to send")
            return False
            
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        return False


def get_fcm_tokens_by_type(notification_type, target_user_ids=None, target_role_ids=None):
    """
    Get FCM tokens based on notification type
    Args:
        notification_type: Type of notification ('all', 'specific', 'role')
        target_user_ids: List of user IDs for 'specific' type
        target_role_ids: List of role IDs for 'role' type
    Returns:
        List of FCM tokens
    """
    try:
        if notification_type == 'all':
            # Get all active users' FCM tokens
            fcm_tokens = User.objects.filter(
                is_active=True,
                fcm_token__isnull=False
            ).exclude(fcm_token='').values_list('fcm_token', flat=True)
            
        elif notification_type == 'specific' and target_user_ids:
            # Get specific users' FCM tokens
            fcm_tokens = User.objects.filter(
                id__in=target_user_ids,
                is_active=True,
                fcm_token__isnull=False
            ).exclude(fcm_token='').values_list('fcm_token', flat=True)
            
        elif notification_type == 'role' and target_role_ids:
            # Get users with specific roles' FCM tokens
            fcm_tokens = User.objects.filter(
                groups__id__in=target_role_ids,
                is_active=True,
                fcm_token__isnull=False
            ).exclude(fcm_token='').values_list('fcm_token', flat=True)
            
        else:
            logger.warning(f"Invalid notification type or missing parameters: {notification_type}")
            return []
        
        return list(fcm_tokens)
        
    except Exception as e:
        logger.error(f"Error getting FCM tokens: {e}")
        return []


def send_notification_to_user_notifications(notification):
    """
    Send push notification to users who have UserNotification records
    Args:
        notification: Notification instance
    """
    try:
        # Get FCM tokens from UserNotification records
        fcm_tokens = UserNotification.objects.filter(
            notification=notification,
            user__is_active=True,
            user__fcm_token__isnull=False
        ).exclude(
            user__fcm_token=''
        ).values_list('user__fcm_token', flat=True)
        
        if not fcm_tokens:
            logger.warning(f"No FCM tokens found for notification {notification.id}")
            return False
        
        # Create messages
        messages = []
        for token in fcm_tokens:
            if token:  # Only send to valid tokens
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=notification.title,
                        body=notification.message,
                    ),
                    data={
                        'notificationId': str(notification.id),
                        'type': notification.type
                    },
                    token=token,
                )
                messages.append(message)
        
        if messages:
            # Send notifications in batches
            response = messaging.send_all(messages)
            logger.info(f"Successfully sent {response.success_count} notifications for notification {notification.id}, {response.failure_count} failed")
            return True
        else:
            logger.warning(f"No valid messages to send for notification {notification.id}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending notification to user notifications: {e}")
        return False
