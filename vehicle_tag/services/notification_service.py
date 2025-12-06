"""
Notification Service for Vehicle Tag Alerts
Sends FCM notifications and SMS when vehicle tag alerts are created
"""
import logging
from vehicle_tag.models import VehicleTag, VehicleTagAlert
from shared.models import Notification, UserNotification
from api_common.utils.sms_service import sms_service

logger = logging.getLogger(__name__)


def send_vehicle_tag_alert_notification(vehicle_tag_alert):
    """
    Send FCM notification and SMS to vehicle tag owner when alert is created
    
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
        
        # Get alert type display name
        alert_display = vehicle_tag_alert.get_alert_display()
        
        # Create notification title and message
        title = f"Vehicle Tag Alert"
        message = f"{alert_display} reported for vehicle tag {vehicle_tag.vtid}"
        
        if vehicle_tag.registration_no:
            message = f"{alert_display} reported for vehicle {vehicle_tag.registration_no}   - Luna IOT"
        
        # Create notification in database
        try:
            # For vehicle tag alerts, use the vehicle tag owner as sentBy
            # If no user is assigned, we can't create notification
            notification = Notification.objects.create(
                title=title,
                message=message,
                type='specific',
                sentBy=user  # Use vehicle tag owner as the sender
            )
            
            # Create user notification
            UserNotification.objects.create(
                notification=notification,
                user=user,
                isRead=False
            )
            
            # Send FCM notification via Node.js API
            fcm_sent = False
            if user.fcm_token and user.fcm_token.strip():  # Check for both None and empty string
                try:
                    from api_common.services.nodejs_notification_service import send_push_notification_via_nodejs
                    fcm_sent = send_push_notification_via_nodejs(
                        notification_id=notification.id,
                        title=title,
                        message=message,
                        target_user_ids=[user.id]
                    )
                    if fcm_sent:
                        logger.info(f"Successfully sent FCM notification via Node.js API to user {user.id} for vehicle tag alert {vehicle_tag_alert.id}")
                    else:
                        logger.warning(f"Failed to send FCM notification via Node.js API to user {user.id} for vehicle tag alert {vehicle_tag_alert.id}")
                except Exception as fcm_error:
                    logger.error(f"Error sending FCM notification via Node.js API to user {user.id}: {fcm_error}")
            else:
                logger.info(f"User {user.id} has no valid FCM token, skipping FCM notification")
            
            # Send SMS to sms_number if present
            sms_sent = False
            if vehicle_tag.sms_number and vehicle_tag.sms_number.strip():
                try:
                    sms_message = f"{alert_display} Alert: {message}"
                    sms_result = sms_service.send_sms(vehicle_tag.sms_number, sms_message)
                    sms_sent = sms_result.get('success', False)
                    if sms_sent:
                        # Update alert to mark SMS as sent
                        vehicle_tag_alert.sms_sent = True
                        vehicle_tag_alert.save(update_fields=['sms_sent'])
                        logger.info(f"Successfully sent SMS to {vehicle_tag.sms_number} for vehicle tag alert {vehicle_tag_alert.id}")
                    else:
                        logger.warning(f"Failed to send SMS to {vehicle_tag.sms_number}: {sms_result.get('message', 'Unknown error')}")
                except Exception as sms_error:
                    logger.error(f"Error sending SMS to {vehicle_tag.sms_number}: {sms_error}")
            else:
                logger.info(f"Vehicle tag {vehicle_tag.vtid} has no SMS number configured, skipping SMS")
            
            # Return True if at least one notification method succeeded
            return fcm_sent or sms_sent
                
        except Exception as e:
            logger.error(f"Error creating notification for vehicle tag alert {vehicle_tag_alert.id}: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending vehicle tag alert notification: {e}")
        return False

