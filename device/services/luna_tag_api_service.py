import hashlib
import requests
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

API_KEY = '123'
API_SECRET = 'fitApp2025-855550-77536756780035706067'
API_URL = 'https://server.findtag.top/fit/openapi/deviceData/v1'


def get_sign(params: Dict) -> str:
    """
    Generate MD5 sign from parameters
    """
    # Exclude timestamp, apikey, and sign from the rest
    rest_params = {k: v for k, v in params.items() if k not in ['timestamp', 'apikey', 'sign']}
    
    # Add timestamp
    import time
    rest_params['timestamp'] = int(time.time())
    
    # Sort and build sign string (key=value&)
    sign_parts = []
    for key in sorted(rest_params.keys()):
        sign_parts.append(f"{key}={rest_params[key]}")
    
    sign_string = "&".join(sign_parts)
    if sign_string:
        sign_string += "&"
    
    # Build final sign string: apikey=...&apisecret=...&sign_string (remove last &)
    new_sign = f"apikey={API_KEY}&apisecret={API_SECRET}&{sign_string}"
    # Remove the last & if present
    if new_sign.endswith('&'):
        new_sign = new_sign[:-1]
    
    # Generate MD5 hash and convert to uppercase
    md5_hash = hashlib.md5(new_sign.encode('utf-8')).hexdigest().upper()
    
    return md5_hash


def get_body_payload(public_key: str) -> Dict:
    """
    Build request payload with dynamic timestamp
    """
    import time
    
    payload = {
        'apikey': API_KEY,
        'timestamp': int(time.time()),
        'nonce': '123456',
        'sign': '',
        'publicKey': public_key,
        'timePeriod': 0,
    }
    
    # Generate sign
    payload['sign'] = get_sign(payload)
    
    return payload


def fetch_tag_data(public_key: str) -> Optional[Dict]:
    """
    Make API call to fetch tag data
    Returns parsed data or None on error
    """
    try:
        payload = get_body_payload(public_key)
        
        # Build query string
        query_params = '&'.join([f"{k}={v}" for k, v in payload.items()])
        url = f"{API_URL}?{query_params}"
        
        logger.info(f"Fetching data for publicKey: {public_key}")
        
        # Make request
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('code') != 0:
            logger.error(f"API returned error: {data.get('message', 'Unknown error')}")
            return None
        
        # Parse response data
        data_list = data.get('data', [])
        if not data_list:
            logger.warning(f"No data returned for publicKey: {public_key}")
            return None
        
        # Get first item from data array
        tag_data = data_list[0]
        
        # Parse coordinate (format: "latitude,longitude")
        coordinate = tag_data.get('coordinate', '')
        latitude = None
        longitude = None
        
        if coordinate:
            try:
                coords = coordinate.split(',')
                if len(coords) >= 2:
                    latitude = float(coords[0].strip())
                    longitude = float(coords[1].strip())
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing coordinate '{coordinate}': {e}")
        
        return {
            'battery': tag_data.get('batteryLevel', ''),
            'latitude': latitude,
            'longitude': longitude,
            'privateKey': tag_data.get('privateKey', ''),
            'collectionTime': tag_data.get('collectionTime', None),
            'status': tag_data.get('status', ''),
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for publicKey {public_key}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching data for publicKey {public_key}: {e}")
        return None

