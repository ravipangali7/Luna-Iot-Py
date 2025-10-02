import firebase_admin
from firebase_admin import credentials, messaging
import os
from luna_iot_py.settings import BASE_DIR
from core.models.user import User
from shared.models import Notification, UserNotification
from django.db.models import Q
import logging
import time

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
FIREBASE_INITIALIZED = False

def initialize_firebase():
    """
    Initialize Firebase Admin SDK, removing any existing app first
    """
    global FIREBASE_INITIALIZED
    
    try:
        # Remove any existing Firebase app first
        try:
            # Get all existing apps
            existing_apps = firebase_admin._apps
            for app_name, app in existing_apps.items():
                try:
                    firebase_admin.delete_app(app)
                    logger.info(f"Removed existing Firebase app: {app_name}")
                except Exception as e:
                    logger.warning(f"Could not remove app {app_name}: {e}")
        except Exception as e:
            logger.warning(f"Error removing existing apps: {e}")
            # Try to get default app and remove it
            try:
                existing_app = firebase_admin.get_app()
                firebase_admin.delete_app(existing_app)
                logger.info("Removed default Firebase app")
            except ValueError:
                # No existing app, which is fine
                pass
        
        # Small delay to ensure app deletion is complete
        time.sleep(0.1)
        
        # Check if firebase-service.json exists
        firebase_config_path = os.path.join(BASE_DIR, 'firebase-service.json')
        if not os.path.exists(firebase_config_path):
            logger.error(f"Firebase service account key not found at: {firebase_config_path}")
            logger.error("Please ensure firebase-service.json is in the project root directory.")
            FIREBASE_INITIALIZED = False
            return False
        
        # Initialize Firebase with fresh app
        try:
            cred = credentials.Certificate(firebase_config_path)
            firebase_admin.initialize_app(cred)
            FIREBASE_INITIALIZED = True
            logger.info("Firebase Admin SDK initialized successfully")
            return True
        except Exception as cred_error:
            logger.error(f"Failed to load Firebase credentials: {cred_error}")
            logger.error("Please check that firebase-service.json is valid and contains proper service account credentials.")
            FIREBASE_INITIALIZED = False
            return False
        
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
        FIREBASE_INITIALIZED = False
        return False

# Initialize Firebase on module import
initialize_firebase()


def reinitialize_firebase():
    """
    Reinitialize Firebase Admin SDK
    """
    return initialize_firebase()


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
    # Check if Firebase is initialized, if not try to reinitialize
    if not FIREBASE_INITIALIZED:
        logger.warning("Firebase not initialized, attempting to reinitialize...")
        if not reinitialize_firebase():
            logger.warning("Firebase not available - push notifications disabled. Notification saved to database only.")
            return True  # Return True to not break the notification creation flow
    
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
            try:
                logger.info(f"Attempting to send {len(messages)} Firebase messages")
                response = messaging.send_all(messages)
                logger.info(f"Successfully sent {response.success_count} notifications, {response.failure_count} failed")
                
                # Log any failures for debugging
                if response.failure_count > 0:
                    for i, response in enumerate(response.responses):
                        if not response.success:
                            logger.error(f"Failed to send message {i}: {response.exception}")
                
                return True
            except Exception as send_error:
                logger.error(f"Error sending Firebase messages: {send_error}")
                logger.error(f"Error type: {type(send_error).__name__}")
                # If it's a 404 error, it means Firebase is not properly configured
                if "404" in str(send_error) or "batch" in str(send_error).lower():
                    logger.warning("Firebase configuration issue detected. Push notifications disabled.")
                    return True  # Return True to not break the flow
                return False
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
    # Check if Firebase is initialized, if not try to reinitialize
    if not FIREBASE_INITIALIZED:
        logger.warning("Firebase not initialized, attempting to reinitialize...")
        if not reinitialize_firebase():
            logger.warning("Firebase not available - push notifications disabled. Notification saved to database only.")
            return True  # Return True to not break the notification creation flow
    
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
            try:
                response = messaging.send_all(messages)
                logger.info(f"Successfully sent {response.success_count} notifications for notification {notification.id}, {response.failure_count} failed")
                return True
            except Exception as send_error:
                logger.error(f"Error sending Firebase messages for notification {notification.id}: {send_error}")
                # If it's a 404 error, it means Firebase is not properly configured
                if "404" in str(send_error) or "batch" in str(send_error).lower():
                    logger.warning("Firebase configuration issue detected. Push notifications disabled.")
                    return True  # Return True to not break the flow
                return False
        else:
            logger.warning(f"No valid messages to send for notification {notification.id}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending notification to user notifications: {e}")
        return False
