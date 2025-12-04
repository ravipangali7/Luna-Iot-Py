"""
Notification Service for Vehicle Tag Alerts
Sends FCM notifications when vehicle tag alerts are created
"""
import logging
from vehicle_tag.models import VehicleTag, VehicleTagAlert
from shared.models import Notification, UserNotification

logger = logging.getLogger(__name__)


def send_vehicle_tag_alert_notification(vehicle_tag_alert):
    """
    Send FCM notification to vehicle tag owner when alert is created
    
    Args:
        vehicle_tag_alert: VehicleTagAlert instance
    
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    try:
        vehicle_tag = vehicle_tag_alert.vehicle_tag
        
        # Check if vehicle tag has a user assigned
        if not vehicle_tag.user:
            logger.info(f"Vehicle tag {vehicle_tag.vtid} has no user assigned, skipping notification")
            return False
        
        user = vehicle_tag.user
        
        # Check if user has FCM token
        if not user.fcm_token:
            logger.info(f"User {user.id} has no FCM token, skipping notification")
            return False
        
        # Get alert type display name
        alert_display = vehicle_tag_alert.get_alert_display()
        
        # Create notification title and message
        title = f"{alert_display} Alert"
        message = f"Alert reported for vehicle tag {vehicle_tag.vtid}"
        
        if vehicle_tag.registration_no:
            message = f"Alert reported for vehicle {vehicle_tag.registration_no} (Tag: {vehicle_tag.vtid})"
        
        # Create notification in database
        try:
            notification = Notification.objects.create(
                title=title,
                message=message,
                type='specific',
                source='vehicle_tag'
            )
            
            # Create user notification
            UserNotification.objects.create(
                notification=notification,
                user=user,
                is_read=False
            )
            
            # Send FCM notification
            from api_common.services.firebase_service import send_notification_to_user_notifications
            send_result = send_notification_to_user_notifications(notification)
            
            if send_result:
                logger.info(f"Successfully sent notification to user {user.id} for vehicle tag alert {vehicle_tag_alert.id}")
                return True
            else:
                logger.warning(f"Failed to send FCM notification to user {user.id} for vehicle tag alert {vehicle_tag_alert.id}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating notification for vehicle tag alert {vehicle_tag_alert.id}: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending vehicle tag alert notification: {e}")
        return False

