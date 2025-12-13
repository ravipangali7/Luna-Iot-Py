"""
Background tasks for community siren
Handles delayed operations like buzzer relay OFF commands using threading
"""
import logging
import threading
import time
from api_common.utils.tcp_service import tcp_service

logger = logging.getLogger(__name__)


def schedule_relay_off_command(device_imei: str, delay_seconds: int, history_id: int, buzzer_id: int = None, switch_id: int = None):
    """
    Schedule a relay OFF command to be sent after a specified delay using threading.
    
    Args:
        device_imei: IMEI of the device (buzzer or switch)
        delay_seconds: Delay in seconds before sending relay OFF command
        history_id: ID of the community siren history for logging
        buzzer_id: ID of the buzzer for logging (None for switch devices)
        switch_id: ID of the switch for logging (None for buzzer devices)
    """
    # Validate delay_seconds
    if delay_seconds <= 0:
        delay_seconds = 1
    
    # Determine device type for logging
    if buzzer_id is not None:
        device_type = f"Community Siren Buzzer {buzzer_id}"
    elif switch_id is not None:
        device_type = f"Community Siren Switch {switch_id}"
    else:
        device_type = "Community Siren Device"
    
    def send_delayed_relay_off():
        try:
            # Sleep for the specified delay
            time.sleep(delay_seconds)
            
            # Send relay OFF command via TCP
            relay_off_result = tcp_service.send_relay_off_command(device_imei)
            
            if relay_off_result['success']:
                logger.info(f"[SUCCESS] {device_type} - Relay OFF command sent to device (IMEI: {device_imei}) for history {history_id}")
            else:
                logger.warning(f"[FAILED] {device_type} - Failed to send relay OFF command to device (IMEI: {device_imei}): {relay_off_result['message']}")
                
        except Exception as e:
            logger.error(f"[ERROR] {device_type} - Error in delayed relay OFF command for history {history_id}: {e}")
    
    # Start the delayed task in a separate daemon thread
    thread = threading.Thread(target=send_delayed_relay_off)
    thread.daemon = True  # Daemon thread will not prevent program exit
    thread.start()

