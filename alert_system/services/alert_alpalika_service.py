"""
Service to send alert data to Alpalika API
"""
import requests
import json
import logging
from alert_system.models import AlertHistory

logger = logging.getLogger(__name__)

# Alpalika API configuration
ALPALIKA_API_URL = "https://alert.alpalika.com/api/v1/disaster/incident/"

# API Headers (as specified)
ALPALIKA_API_HEADERS = {
    'content-type': 'application/json',
    'X-API-KEY': 'a1d2f3b4c5e6g7h8i9j0k1l2m3n4o5p6',
    'X-API-TIMESTAMP': '1762248342227',
    'X-API-SIGNATURE': '05664d80c4f59e1c837c49608f7124ffc900c31e55b7421bb42f6d308796c3f3'
}

# Hardcoded values
ALPALIKA_SERVICE = "1"
ALPALIKA_CITIZEN = "86699c62-113e-474b-863f-410b7c031fb6"


def send_alert_to_alpalika(alert_history: AlertHistory) -> bool:
    """
    Send alert data to Alpalika API when institute matches "ललितपुर महानगरपालिका"
    
    Args:
        alert_history: AlertHistory instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Convert DecimalField to string for API
        lat_str = str(alert_history.latitude)
        lng_str = str(alert_history.longitude)
        
        # Build request body
        payload = {
            "location": {
                "lat": lat_str,
                "lng": lng_str
            },
            "service": ALPALIKA_SERVICE,
            "contact_no": alert_history.primary_phone,
            "message": alert_history.name,
            "citizen": ALPALIKA_CITIZEN,
            "device_location": {
                "lat": lat_str,
                "lng": lng_str
            }
        }
        
        logger.info(f"Sending alert {alert_history.id} to Alpalika API")
        logger.debug(f"Alpalika API payload: {json.dumps(payload, indent=2)}")
        
        # Make POST request
        response = requests.post(
            ALPALIKA_API_URL,
            json=payload,
            headers=ALPALIKA_API_HEADERS,
            timeout=30  # 30 second timeout
        )
        
        if response.status_code == 200 or response.status_code == 201:
            response_data = response.json()
            logger.info(f"Successfully sent alert {alert_history.id} to Alpalika API")
            logger.debug(f"Alpalika API response: {json.dumps(response_data, indent=2)}")
            return True
        else:
            logger.error(
                f"Alpalika API request failed for alert {alert_history.id}. "
                f"Status: {response.status_code}, Response: {response.text}"
            )
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error sending alert {alert_history.id} to Alpalika API: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending alert {alert_history.id} to Alpalika API: {e}")
        return False

