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
    # Validate delay_seconds
    if delay_seconds <= 0:
        delay_seconds = 1
    
    def send_delayed_relay_off():
        try:
            # Sleep for the specified delay
            time.sleep(delay_seconds)
            
            
            relay_off_result = sms_service.send_relay_off_command(device_phone)
            
            if relay_off_result['success']:
                pass
            else:
                print(f"[FAILED] Buzzer {buzzer_id} - Failed to send relay OFF command to {device_phone}: {relay_off_result['message']}")
                
        except Exception as e:
            print(f"[ERROR] Buzzer {buzzer_id} - Error in delayed relay OFF command for alert {alert_history_id}: {e}")
    
    # Start the delayed task in a separate daemon thread
    thread = threading.Thread(target=send_delayed_relay_off)
    thread.daemon = True  # Daemon thread will not prevent program exit
    thread.start()
    