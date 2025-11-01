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
    original_delay = delay_seconds
    if delay_seconds <= 0:
        delay_seconds = 1
        print(f"[DEBUG SMS] schedule_relay_off_command() - Invalid delay {original_delay}, using default 1 second")
    
    print(f"[DEBUG SMS] schedule_relay_off_command() - Scheduling relay OFF for buzzer {buzzer_id}, device: {device_phone}, delay: {delay_seconds}s, alert: {alert_history_id}")
    
    def send_delayed_relay_off():
        try:
            print(f"[DEBUG SMS] schedule_relay_off_command() - Thread started for buzzer {buzzer_id}, waiting {delay_seconds}s before sending relay OFF to {device_phone}")
            # Sleep for the specified delay
            time.sleep(delay_seconds)
            
            print(f"[DEBUG SMS] schedule_relay_off_command() - Delay completed, sending relay OFF command to {device_phone} for buzzer {buzzer_id}")
            relay_off_result = sms_service.send_relay_off_command(device_phone)
            print(f"[DEBUG SMS] schedule_relay_off_command() - Relay OFF result for buzzer {buzzer_id}: success={relay_off_result.get('success')}, message={relay_off_result.get('message')}")
            
            if relay_off_result['success']:
                print(f"[DEBUG SMS] schedule_relay_off_command() - Successfully sent delayed relay OFF to {device_phone} for buzzer {buzzer_id} (alert {alert_history_id})")
            else:
                print(f"[DEBUG SMS] schedule_relay_off_command() - [FAILED] Buzzer {buzzer_id} - Failed to send relay OFF command to {device_phone}: {relay_off_result['message']}")
                
        except Exception as e:
            print(f"[DEBUG SMS] schedule_relay_off_command() - [ERROR] Buzzer {buzzer_id} - Error in delayed relay OFF command for alert {alert_history_id}: {e}")
    
    # Start the delayed task in a separate daemon thread
    print(f"[DEBUG SMS] schedule_relay_off_command() - Starting background thread for buzzer {buzzer_id}")
    thread = threading.Thread(target=send_delayed_relay_off)
    thread.daemon = True  # Daemon thread will not prevent program exit
    thread.start()
    print(f"[DEBUG SMS] schedule_relay_off_command() - Background thread started for buzzer {buzzer_id}")
    