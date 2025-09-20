"""
Firebase Cloud Messaging service for sending push notifications
"""
import os
import logging
from typing import Dict, List, Any, Optional
from django.conf import settings

# Try to import Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    firebase_admin = None
    credentials = None
    messaging = None

logger = logging.getLogger(__name__)


class FirebaseService:
    """Firebase Cloud Messaging service"""
    
    def __init__(self):
        self.app = None
        self.initialized = False
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        if not FIREBASE_AVAILABLE:
            logger.error("Firebase Admin SDK not available")
            return
        
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                self.app = firebase_admin.get_app()
                self.initialized = True
                return
            
            # Load from Django settings
            project_id = getattr(settings, 'FIREBASE_PROJECT_ID', '')
            client_email = getattr(settings, 'FIREBASE_CLIENT_EMAIL', '')
            private_key = getattr(settings, 'FIREBASE_PRIVATE_KEY', '')
            
            if not all([project_id, client_email, private_key]):
                logger.error("Firebase credentials not found in Django settings")
                return
            
            # Replace escaped newlines in private key
            if private_key:
                private_key = private_key.replace('\\n', '\n')
            
            # Create credentials from environment variables
            cred = credentials.Certificate({
                'project_id': project_id,
                'client_email': client_email,
                'private_key': private_key
            })
            
            # Initialize Firebase Admin SDK
            self.app = firebase_admin.initialize_app(cred)
            self.initialized = True
            logger.info("Firebase Admin SDK initialized successfully")
            
        except Exception as e:
            logger.error(f"Firebase initialization error: {e}")
            self.initialized = False
    
    def send_notification_to_single_user(self, fcm_token: str, title: str, message: str, data: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Send notification to a single user
        Args:
            fcm_token: FCM token of the user
            title: Notification title
            message: Notification message
            data: Additional data payload
        Returns:
            Dict with success status and message ID or error
        """
        if not self.initialized:
            return {"success": False, "error": "Firebase not initialized"}
        
        try:
            message_payload = messaging.Message(
                token=fcm_token,
                notification=messaging.Notification(
                    title=title,
                    body=message,
                ),
                data=data or {},
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='luna_iot_channel',
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                        ),
                    ),
                ),
            )
            
            response = messaging.send(message_payload)
            return {"success": True, "messageId": response}
            
        except Exception as e:
            logger.error(f"Error sending notification to single user: {e}")
            return {"success": False, "error": str(e)}
    
    def send_notification_to_multiple_users(self, fcm_tokens: List[str], title: str, message: str, data: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Send notification to multiple users
        Args:
            fcm_tokens: List of FCM tokens
            title: Notification title
            message: Notification message
            data: Additional data payload
        Returns:
            Dict with success status and counts
        """
        if not self.initialized:
            return {"success": False, "error": "Firebase not initialized"}
        
        if not fcm_tokens:
            return {"success": False, "error": "No FCM tokens provided"}
        
        try:
            message_payload = messaging.MulticastMessage(
                tokens=fcm_tokens,
                notification=messaging.Notification(
                    title=title,
                    body=message,
                ),
                data=data or {},
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='luna_iot_channel',
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                        ),
                    ),
                ),
            )
            
            response = messaging.send_multicast(message_payload)
            return {
                "success": True,
                "successCount": response.success_count,
                "failureCount": response.failure_count,
                "responses": [r.success for r in response.responses]
            }
            
        except Exception as e:
            logger.error(f"Error sending notification to multiple users: {e}")
            return {"success": False, "error": str(e)}
    
    def send_notification_to_topic(self, topic: str, title: str, message: str, data: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Send notification to a topic
        Args:
            topic: Topic name
            title: Notification title
            message: Notification message
            data: Additional data payload
        Returns:
            Dict with success status and message ID or error
        """
        if not self.initialized:
            return {"success": False, "error": "Firebase not initialized"}
        
        try:
            message_payload = messaging.Message(
                topic=topic,
                notification=messaging.Notification(
                    title=title,
                    body=message,
                ),
                data=data or {},
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='luna_iot_channel',
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                        ),
                    ),
                ),
            )
            
            response = messaging.send(message_payload)
            return {"success": True, "messageId": response}
            
        except Exception as e:
            logger.error(f"Error sending notification to topic: {e}")
            return {"success": False, "error": str(e)}


# Create singleton instance
firebase_service = FirebaseService()