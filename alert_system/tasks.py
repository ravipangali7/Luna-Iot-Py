"""
Background tasks for alert system
Handles delayed operations like buzzer relay OFF commands using threading
"""
import logging
import threading
import time
from api_common.utils.tcp_service import tcp_service

logger = logging.getLogger(__name__)


def schedule_relay_off_command(device_imei: str, delay_seconds: int, alert_history_id: int, buzzer_id: int = None):
    """
    Schedule a relay OFF command to be sent after a specified delay using threading.
    
    Args:
        device_imei: IMEI of the device (buzzer or switch)
        delay_seconds: Delay in seconds before sending relay OFF command
        alert_history_id: ID of the alert history for logging
        buzzer_id: ID of the buzzer for logging (None for switch devices)
    """
    # Validate delay_seconds
    if delay_seconds <= 0:
        delay_seconds = 1
    
    # Determine device type for logging
    device_type = "Switch device" if buzzer_id is None else f"Buzzer {buzzer_id}"
    
    def send_delayed_relay_off():
        try:
            # Sleep for the specified delay
            time.sleep(delay_seconds)
            
            # Send relay OFF command via TCP
            relay_off_result = tcp_service.send_relay_off_command(device_imei)
            
            if relay_off_result['success']:
                logger.info(f"[SUCCESS] {device_type} - Relay OFF command sent to device (IMEI: {device_imei}) for alert {alert_history_id}")
            else:
                logger.warning(f"[FAILED] {device_type} - Failed to send relay OFF command to device (IMEI: {device_imei}): {relay_off_result['message']}")
                
        except Exception as e:
            logger.error(f"[ERROR] {device_type} - Error in delayed relay OFF command for alert {alert_history_id}: {e}")
    
    # Start the delayed task in a separate daemon thread
    thread = threading.Thread(target=send_delayed_relay_off)
    thread.daemon = True  # Daemon thread will not prevent program exit
    thread.start()
    