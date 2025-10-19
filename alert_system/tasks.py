"""
Background tasks for alert system
Handles delayed operations like buzzer relay OFF commands
"""
import logging
from celery import shared_task
from api_common.utils.sms_service import sms_service

logger = logging.getLogger(__name__)


@shared_task
def schedule_relay_off_command(device_phone: str, delay_seconds: int, alert_history_id: int, buzzer_id: int):
    """
    Schedule a relay OFF command to be sent after a specified delay.
    
    Args:
        device_phone: Phone number of the buzzer device
        delay_seconds: Delay in seconds before sending relay OFF command
        alert_history_id: ID of the alert history for logging
        buzzer_id: ID of the buzzer for logging
        
    Returns:
        Dict with success status and details
    """
    try:
        logger.info(f"Scheduling relay OFF command for buzzer {buzzer_id} after {delay_seconds} seconds (alert {alert_history_id})")
        
        # Send relay OFF command
        relay_off_result = sms_service.send_relay_off_command(device_phone)
        
        if relay_off_result['success']:
            logger.info(f"Relay OFF command sent successfully to buzzer {buzzer_id} ({device_phone}) for alert {alert_history_id}")
            return {
                'success': True,
                'message': f'Relay OFF command sent successfully after {delay_seconds} seconds',
                'device_phone': device_phone,
                'buzzer_id': buzzer_id,
                'alert_history_id': alert_history_id,
                'delay_seconds': delay_seconds
            }
        else:
            logger.warning(f"Failed to send relay OFF command to buzzer {buzzer_id} ({device_phone}): {relay_off_result['message']}")
            return {
                'success': False,
                'message': f"Failed to send relay OFF command: {relay_off_result['message']}",
                'device_phone': device_phone,
                'buzzer_id': buzzer_id,
                'alert_history_id': alert_history_id,
                'delay_seconds': delay_seconds
            }
            
    except Exception as e:
        logger.error(f"Error in scheduled relay OFF command for buzzer {buzzer_id} (alert {alert_history_id}): {e}")
        return {
            'success': False,
            'message': str(e),
            'device_phone': device_phone,
            'buzzer_id': buzzer_id,
            'alert_history_id': alert_history_id,
            'delay_seconds': delay_seconds
        }


# Fallback implementation using threading if Celery is not available
def schedule_relay_off_command_fallback(device_phone: str, delay_seconds: int, alert_history_id: int, buzzer_id: int):
    """
    Fallback implementation using threading.Timer if Celery is not available.
    
    Args:
        device_phone: Phone number of the buzzer device
        delay_seconds: Delay in seconds before sending relay OFF command
        alert_history_id: ID of the alert history for logging
        buzzer_id: ID of the buzzer for logging
    """
    import threading
    import time
    
    def send_delayed_relay_off():
        try:
            time.sleep(delay_seconds)
            relay_off_result = sms_service.send_relay_off_command(device_phone)
            
            if relay_off_result['success']:
                logger.info(f"Relay OFF command sent successfully to buzzer {buzzer_id} ({device_phone}) for alert {alert_history_id}")
            else:
                logger.warning(f"Failed to send relay OFF command to buzzer {buzzer_id} ({device_phone}): {relay_off_result['message']}")
                
        except Exception as e:
            logger.error(f"Error in fallback relay OFF command for buzzer {buzzer_id} (alert {alert_history_id}): {e}")
    
    # Start the timer in a separate thread
    timer = threading.Timer(delay_seconds, send_delayed_relay_off)
    timer.start()
    
    logger.info(f"Scheduled fallback relay OFF command for buzzer {buzzer_id} after {delay_seconds} seconds (alert {alert_history_id})")
