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
            logger.info(f"[THREAD START] Buzzer {buzzer_id} - Thread started for alert {alert_history_id}")
            logger.info(f"[DELAY START] Buzzer {buzzer_id} - Starting delay of {delay_seconds} seconds")
            
            # Sleep for the specified delay
            time.sleep(delay_seconds)
            
            logger.info(f"[DELAY END] Buzzer {buzzer_id} - Delay completed, now sending relay OFF command")
            logger.info(f"[SMS SEND] Buzzer {buzzer_id} - Sending relay OFF command to {device_phone}")
            
            relay_off_result = sms_service.send_relay_off_command(device_phone)
            
            if relay_off_result['success']:
                logger.info(f"[SUCCESS] Buzzer {buzzer_id} - Relay OFF command sent successfully to {device_phone} for alert {alert_history_id}")
            else:
                logger.warning(f"[FAILED] Buzzer {buzzer_id} - Failed to send relay OFF command to {device_phone}: {relay_off_result['message']}")
                
        except Exception as e:
            logger.error(f"[ERROR] Buzzer {buzzer_id} - Error in delayed relay OFF command for alert {alert_history_id}: {e}")
    
    # Start the delayed task in a separate daemon thread
    logger.info(f"[SCHEDULE] Buzzer {buzzer_id} - Creating thread for {delay_seconds} second delay")
    thread = threading.Thread(target=send_delayed_relay_off)
    thread.daemon = True  # Daemon thread will not prevent program exit
    thread.start()
    
    # Verify thread is alive
    if thread.is_alive():
        logger.info(f"[SCHEDULED] Buzzer {buzzer_id} - Thread started successfully and is alive, relay OFF will be sent after {delay_seconds} seconds (alert {alert_history_id})")
    else:
        logger.error(f"[ERROR] Buzzer {buzzer_id} - Thread failed to start properly!")
