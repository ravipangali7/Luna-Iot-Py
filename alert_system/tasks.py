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
        print(f"[WARNING] Buzzer {buzzer_id} - Invalid delay value: {delay_seconds} seconds. Using 1 second minimum.")
        delay_seconds = 1
    
    print(f"[VALIDATION] Buzzer {buzzer_id} - Using delay of {delay_seconds} seconds")
    def send_delayed_relay_off():
        try:
            print(f"[THREAD START] Buzzer {buzzer_id} - Thread started for alert {alert_history_id}")
            print(f"[DELAY START] Buzzer {buzzer_id} - Starting delay of {delay_seconds} seconds")
            
            # Sleep for the specified delay
            time.sleep(delay_seconds)
            
            print(f"[DELAY END] Buzzer {buzzer_id} - Delay completed, now sending relay OFF command")
            print(f"[SMS SEND] Buzzer {buzzer_id} - Sending relay OFF command to {device_phone}")
            
            relay_off_result = sms_service.send_relay_off_command(device_phone)
            
            if relay_off_result['success']:
                print(f"[SUCCESS] Buzzer {buzzer_id} - Relay OFF command sent successfully to {device_phone} for alert {alert_history_id}")
            else:
                print(f"[FAILED] Buzzer {buzzer_id} - Failed to send relay OFF command to {device_phone}: {relay_off_result['message']}")
                
        except Exception as e:
            print(f"[ERROR] Buzzer {buzzer_id} - Error in delayed relay OFF command for alert {alert_history_id}: {e}")
    
    # Start the delayed task in a separate daemon thread
    print(f"[SCHEDULE] Buzzer {buzzer_id} - Creating thread for {delay_seconds} second delay")
    thread = threading.Thread(target=send_delayed_relay_off)
    thread.daemon = True  # Daemon thread will not prevent program exit
    thread.start()
    
    # Verify thread is alive
    if thread.is_alive():
        print(f"[SCHEDULED] Buzzer {buzzer_id} - Thread started successfully and is alive, relay OFF will be sent after {delay_seconds} seconds (alert {alert_history_id})")
    else:
        print(f"[ERROR] Buzzer {buzzer_id} - Thread failed to start properly!")
