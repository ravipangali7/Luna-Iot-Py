"""
Service to send push notifications via Node.js API
"""
import requests
import json
import logging
from django.conf import settings
from core.models import User
from shared.models import Notification, UserNotification

logger = logging.getLogger(__name__)

# Node.js API configuration
NODEJS_API_BASE_URL = getattr(settings, 'NODEJS_API_BASE_URL', 'https://www.system.mylunago.com')
NODEJS_PUSH_NOTIFICATION_ENDPOINT = f"{NODEJS_API_BASE_URL}/api/push-notification"

def send_push_notification_via_nodejs(notification_id, title, message, target_user_ids=None):
    """
    Send push notification via Node.js API
    
    Args:
        notification_id: ID of the notification
        title: Notification title
        message: Notification message
        target_user_ids: List of user IDs to send to (optional, if None sends to all users with FCM tokens)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get FCM tokens from users
        fcm_tokens = []
        
        if target_user_ids:
            # Get specific users' FCM tokens
            users = User.objects.filter(
                id__in=target_user_ids,
                is_active=True,
                fcm_token__isnull=False
            ).exclude(fcm_token='')
            
            fcm_tokens = [user.fcm_token for user in users if user.fcm_token]
        else:
            # Get all active users' FCM tokens
            users = User.objects.filter(
                is_active=True,
                fcm_token__isnull=False
            ).exclude(fcm_token='')
            
            fcm_tokens = [user.fcm_token for user in users if user.fcm_token]
        
        if not fcm_tokens:
            logger.warning(f"No FCM tokens found for notification {notification_id}")
            return False
        
        # Prepare payload for Node.js API
        payload = {
            "title": title,
            "message": message,
            "tokens": fcm_tokens
        }
        
        # Send request to Node.js API
        headers = {
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Sending push notification to Node.js API for notification {notification_id}")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            NODEJS_PUSH_NOTIFICATION_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=30  # 30 second timeout
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('success'):
                logger.info(f"Successfully sent push notification via Node.js API for notification {notification_id}")
                logger.info(f"Response: {response_data}")
                return True
            else:
                logger.error(f"Node.js API returned error for notification {notification_id}: {response_data}")
                return False
        else:
            logger.error(f"Node.js API request failed for notification {notification_id}. Status: {response.status_code}, Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error sending push notification via Node.js API for notification {notification_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending push notification via Node.js API for notification {notification_id}: {e}")
        return False


def send_push_notification_to_user_notifications(notification):
    """
    Send push notification to all users who have UserNotification records for this notification
    
    Args:
        notification: Notification instance
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get all users who have UserNotification records for this notification
        user_notifications = UserNotification.objects.filter(notification=notification)
        target_user_ids = [un.user.id for un in user_notifications if un.user.is_active]
        
        if not target_user_ids:
            logger.warning(f"No active users found for notification {notification.id}")
            return False
        
        return send_push_notification_via_nodejs(
            notification_id=notification.id,
            title=notification.title,
            message=notification.message,
            target_user_ids=target_user_ids
        )
        
    except Exception as e:
        logger.error(f"Error sending push notification to user notifications for notification {notification.id}: {e}")
        return False


def send_push_notification_to_specific_user(notification, user):
    """
    Send push notification to a specific user
    
    Args:
        notification: Notification instance
        user: User instance
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not user.is_active or not user.fcm_token:
            logger.warning(f"User {user.id} is inactive or has no FCM token")
            return False
        
        return send_push_notification_via_nodejs(
            notification_id=notification.id,
            title=notification.title,
            message=notification.message,
            target_user_ids=[user.id]
        )
        
    except Exception as e:
        logger.error(f"Error sending push notification to user {user.id} for notification {notification.id}: {e}")
        return False
