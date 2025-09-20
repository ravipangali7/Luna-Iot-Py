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
        # Don't initialize immediately - wait until first use
    
    def _ensure_initialized(self):
        """Ensure Firebase is initialized before use"""
        if not self.initialized:
            self._initialize_firebase()
        return self.initialized
    
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
            
            # Try to load from service account JSON file first
            service_account_file = self._get_service_account_file_path()
            if service_account_file and os.path.exists(service_account_file):
                logger.info(f"Loading Firebase credentials from file: {service_account_file}")
                cred = credentials.Certificate(service_account_file)
            else:
                # Fallback to Django settings
                logger.info("Loading Firebase credentials from Django settings")
                project_id = getattr(settings, 'FIREBASE_PROJECT_ID', '')
                client_email = getattr(settings, 'FIREBASE_CLIENT_EMAIL', '')
                private_key = getattr(settings, 'FIREBASE_PRIVATE_KEY', '')
                
                logger.info(f"Firebase config - Project ID: {project_id[:10]}..., Email: {client_email[:20]}..., Key: {private_key[:20]}...")
                
                if not all([project_id, client_email, private_key]):
                    logger.error("Firebase credentials not found in service account file or Django settings")
                    return
                
                # Replace escaped newlines in private key
                if private_key:
                    private_key = private_key.replace('\\n', '\n')
                    logger.info(f"Private key length: {len(private_key)}")
                    logger.info(f"Private key starts with: {private_key[:50]}...")
                
                # Create credentials from Django settings
                cred = credentials.Certificate({
                    'type': 'service_account',
                    'project_id': project_id,
                    'private_key_id': getattr(settings, 'FIREBASE_PRIVATE_KEY_ID', ''),
                    'private_key': private_key,
                    'client_email': client_email,
                    'client_id': getattr(settings, 'FIREBASE_CLIENT_ID', ''),
                    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                    'token_uri': 'https://oauth2.googleapis.com/token',
                    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
                    'client_x509_cert_url': f'https://www.googleapis.com/robot/v1/metadata/x509/{client_email}'
                })
            
            # Initialize Firebase Admin SDK
            self.app = firebase_admin.initialize_app(cred)
            self.initialized = True
            logger.info("Firebase Admin SDK initialized successfully")
            
        except Exception as e:
            logger.error(f"Firebase initialization error: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.initialized = False
    
    def _get_service_account_file_path(self):
        """Get the path to the Firebase service account JSON file"""
        # Check multiple possible locations
        possible_paths = [
            os.getenv('FIREBASE_SERVICE_ACCOUNT_FILE'),  # Environment variable
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'firebase-service-account.json'),  # Project root
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'firebase-service-account.json'),  # Config folder
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'secrets', 'firebase-service-account.json'),  # Secrets folder
            'firebase-service-account.json',  # Current directory
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                return path
        
        return None
    
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
        if not self._ensure_initialized():
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
        if not self._ensure_initialized():
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
        if not self._ensure_initialized():
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
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test Firebase connection
        Returns:
            Dict with test results
        """
        if not self._ensure_initialized():
            return {"success": False, "error": "Firebase not initialized"}
        
        try:
            # Try to get the app info
            app_info = self.app.project_id
            return {
                "success": True, 
                "message": f"Firebase connected successfully. Project: {app_info}",
                "project_id": app_info
            }
        except Exception as e:
            return {"success": False, "error": f"Connection test failed: {str(e)}"}


# Create singleton instance
firebase_service = FirebaseService()