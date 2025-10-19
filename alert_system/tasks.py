"""
Background tasks for alert system
Handles delayed operations like buzzer relay OFF commands using threading
"""
import logging
import threading
import time
from api_common.utils.sms_service import sms_service

logger = logging.getLogger(__name__)


def schedule_relay_off_command(device_phone: str, delay_seconds: int, alert_history_id: int, buzzer_id: int):
    """
    Schedule a relay OFF command to be sent after a specified delay using threading.
    
    Args:
        device_phone: Phone number of the buzzer device
        delay_seconds: Delay in seconds before sending relay OFF command
        alert_history_id: ID of the alert history for logging
        buzzer_id: ID of the buzzer for logging
    """
    def send_delayed_relay_off():
        try:
            logger.info(f"Starting delay of {delay_seconds} seconds for buzzer {buzzer_id} (alert {alert_history_id})")
            time.sleep(delay_seconds)
            
            logger.info(f"Sending relay OFF command to buzzer {buzzer_id} ({device_phone}) for alert {alert_history_id}")
            relay_off_result = sms_service.send_relay_off_command(device_phone)
            
            if relay_off_result['success']:
                logger.info(f"Relay OFF command sent successfully to buzzer {buzzer_id} ({device_phone}) for alert {alert_history_id}")
            else:
                logger.warning(f"Failed to send relay OFF command to buzzer {buzzer_id} ({device_phone}): {relay_off_result['message']}")
                
        except Exception as e:
            logger.error(f"Error in delayed relay OFF command for buzzer {buzzer_id} (alert {alert_history_id}): {e}")
    
    # Start the delayed task in a separate daemon thread
    thread = threading.Thread(target=send_delayed_relay_off)
    thread.daemon = True  # Daemon thread will not prevent program exit
    thread.start()
    
    logger.info(f"Scheduled relay OFF command for buzzer {buzzer_id} after {delay_seconds} seconds (alert {alert_history_id})")
