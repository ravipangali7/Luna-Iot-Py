"""
Notification Service for Vehicle Tag Alerts
Sends FCM notifications and SMS when vehicle tag alerts are created
"""
import logging
from decimal import Decimal
from vehicle_tag.models import VehicleTag, VehicleTagAlert
from shared.models import Notification, UserNotification
from api_common.utils.sms_service import sms_service
from api_common.utils.sms_cost_utils import calculate_sms_cost
from finance.models import Wallet
from core.models import MySetting

logger = logging.getLogger(__name__)

# Nepali messages for each alert type
ALERT_NEPALI_MESSAGES = {
    'wrong_parking': 'गलत पार्किङ',
    'blocking_road': 'सडक अवरुद्ध',
    'not_locked_ignition_on': 'लक नभएको / इग्निसन चालू',
    'vehicle_tow_alert': 'गाडी टो गर्ने चेतावनी',
    'traffic_rule_violation': 'यातायात नियम उल्लङ्घन',
    'fire_physical_threat': 'आगो र शारीरिक खतरा',
    'accident_alert': 'दुर्घटना चेतावनी (परिवारलाई सूचना)',
}


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
        
        # Get Nepali alert message, fallback to English if not found
        nepali_alert = ALERT_NEPALI_MESSAGES.get(
            vehicle_tag_alert.alert,
            vehicle_tag_alert.get_alert_display()
        )
        
        # Create notification title and message
        title = f"Vehicle Tag Alert"
        
        # Construct message with Nepali alert text, keeping Vehicle no and Luna IOT in English
        if vehicle_tag.registration_no:
            message = f"{nepali_alert} को रिपोर्ट गाडी .नं {vehicle_tag.registration_no} - Luna IOT"
        else:
            message = f"{nepali_alert} को रिपोर्ट गाडी Tag {vehicle_tag.vtid} - Luna IOT"
        
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
            
            # Determine SMS recipients based on alert type
            sms_recipients = []
            is_accident_alert = vehicle_tag_alert.alert == 'accident_alert'
            
            if is_accident_alert:
                # For Accident Alert: send to both sos_number and sms_number
                if vehicle_tag.sos_number and vehicle_tag.sos_number.strip():
                    sms_recipients.append(vehicle_tag.sos_number.strip())
                if vehicle_tag.sms_number and vehicle_tag.sms_number.strip():
                    sms_recipients.append(vehicle_tag.sms_number.strip())
            else:
                # For other alerts: send only to sms_number
                if vehicle_tag.sms_number and vehicle_tag.sms_number.strip():
                    sms_recipients.append(vehicle_tag.sms_number.strip())
            
            # Remove duplicates while preserving order
            sms_recipients = list(dict.fromkeys(sms_recipients))
            
            # Send SMS if recipients exist
            sms_sent = False
            if sms_recipients:
                try:
                    # Get or create wallet for user
                    wallet, created = Wallet.objects.get_or_create(
                        user=user,
                        defaults={'balance': Decimal('0.00')}
                    )
                    
                    # Get MySetting for SMS price and character price
                    try:
                        my_setting = MySetting.objects.first()
                    except Exception as e:
                        logger.warning(f"Error getting MySetting: {str(e)}")
                        my_setting = None
                    
                    # Determine SMS price: use wallet-specific price if available, otherwise use default from MySetting
                    sms_price = wallet.sms_price
                    if sms_price is None or sms_price == Decimal('0.00'):
                        if my_setting and my_setting.sms_price:
                            sms_price = Decimal(str(my_setting.sms_price))
                        else:
                            sms_price = Decimal('0.00')
                    
                    # Get SMS character price from MySetting (default: 160)
                    sms_character_price = 160  # Default value
                    if my_setting and my_setting.sms_character_price:
                        sms_character_price = int(my_setting.sms_character_price)
                    
                    # Format the final SMS message that will be sent
                    sms_message = f"""Vehicle Tag Alert: 
{message}"""
                    
                    # Calculate total cost based on character count of the FINAL formatted message
                    total_cost, character_count, sms_parts = calculate_sms_cost(
                        message=sms_message,
                        sms_price=sms_price,
                        sms_character_price=sms_character_price,
                        num_recipients=len(sms_recipients)
                    )
                    
                    # Check if wallet balance is sufficient
                    if wallet.balance >= total_cost:
                        # Deduct balance before sending SMS
                        success = wallet.subtract_balance(
                            amount=total_cost,
                            description=f"Vehicle Tag Alert SMS to {len(sms_recipients)} recipient(s)",
                            performed_by=user
                        )
                        
                        if not success:
                            logger.warning(f"Failed to deduct {total_cost} from wallet for user {user.id}, skipping SMS")
                        else:
                            logger.info(f"Deducted {total_cost} from wallet for user {user.id} before sending {len(sms_recipients)} SMS (Message: {character_count} chars, {sms_parts} SMS parts)")
                            
                            successful_sends = 0
                            for recipient in sms_recipients:
                                try:
                                    sms_result = sms_service.send_sms(recipient, sms_message)
                                    if sms_result.get('success', False):
                                        successful_sends += 1
                                        logger.info(f"Successfully sent SMS to {recipient} for vehicle tag alert {vehicle_tag_alert.id}")
                                    else:
                                        logger.warning(f"Failed to send SMS to {recipient}: {sms_result.get('message', 'Unknown error')}")
                                except Exception as sms_error:
                                    logger.error(f"Error sending SMS to {recipient}: {sms_error}")
                            
                            # Mark SMS as sent if at least one SMS was successfully sent
                            if successful_sends > 0:
                                sms_sent = True
                                vehicle_tag_alert.sms_sent = True
                                vehicle_tag_alert.save(update_fields=['sms_sent'])
                                logger.info(f"Successfully sent SMS to {successful_sends}/{len(sms_recipients)} recipients for vehicle tag alert {vehicle_tag_alert.id}")
                            else:
                                logger.warning(f"Failed to send SMS to all recipients for vehicle tag alert {vehicle_tag_alert.id}")
                                # Refund the deducted amount since no SMS was sent
                                wallet.add_balance(
                                    amount=total_cost,
                                    description=f"Refund for failed Vehicle Tag Alert SMS",
                                    performed_by=user
                                )
                    else:
                        # Insufficient balance - skip SMS sending
                        logger.warning(f"Insufficient wallet balance for user {user.id}. Required: {total_cost}, Available: {wallet.balance}")
                        
                        # Create insufficient balance notification
                        try:
                            insufficient_balance_notification = Notification.objects.create(
                                title="Insufficient Wallet Balance",
                                message="you haven't sufficient balance in wallet please deposit balance in wallet for receive sms alert",
                                type='specific',
                                sentBy=user
                            )
                            
                            UserNotification.objects.create(
                                notification=insufficient_balance_notification,
                                user=user,
                                isRead=False
                            )
                            
                            # Send FCM notification for insufficient balance if FCM token exists
                            if user.fcm_token and user.fcm_token.strip():
                                try:
                                    from api_common.services.nodejs_notification_service import send_push_notification_via_nodejs
                                    send_push_notification_via_nodejs(
                                        notification_id=insufficient_balance_notification.id,
                                        title="Insufficient Wallet Balance",
                                        message="you haven't sufficient balance in wallet please deposit balance in wallet for receive sms alert",
                                        target_user_ids=[user.id]
                                    )
                                    logger.info(f"Sent insufficient balance notification to user {user.id}")
                                except Exception as fcm_error:
                                    logger.error(f"Error sending FCM notification for insufficient balance to user {user.id}: {fcm_error}")
                        except Exception as notif_error:
                            logger.error(f"Error creating insufficient balance notification: {notif_error}")
                        
                        # Mark SMS as not sent
                        vehicle_tag_alert.sms_sent = False
                        vehicle_tag_alert.save(update_fields=['sms_sent'])
                        
                except Exception as sms_error:
                    logger.error(f"Error processing SMS for vehicle tag alert {vehicle_tag_alert.id}: {sms_error}")
            else:
                logger.info(f"Vehicle tag {vehicle_tag.vtid} has no SMS recipients configured, skipping SMS")
            
            # Return True if at least one notification method succeeded
            return fcm_sent or sms_sent
                
        except Exception as e:
            logger.error(f"Error creating notification for vehicle tag alert {vehicle_tag_alert.id}: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending vehicle tag alert notification: {e}")
        return False

