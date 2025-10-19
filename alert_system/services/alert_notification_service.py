"""
Service to send real-time alert notifications via Node.js API
"""
import requests
import json
import logging
from django.conf import settings
from alert_system.models import AlertHistory, AlertRadar, AlertGeofence

logger = logging.getLogger(__name__)

# Node.js API configuration
NODEJS_API_BASE_URL = getattr(settings, 'NODEJS_API_BASE_URL', 'https://www.system.mylunago.com')
NODEJS_ALERT_NOTIFICATION_ENDPOINT = f"{NODEJS_API_BASE_URL}/api/alert-notification"


def is_point_in_polygon(lat, lng, boundary):
    """
    Check if a point is inside a polygon using ray casting algorithm
    
    Args:
        lat: Point latitude
        lng: Point longitude
        boundary: GeoJSON boundary object or list of coordinates
    
    Returns:
        bool: True if point is inside polygon
    """
    try:
        if not boundary:
            return False
        
        # Handle GeoJSON format
        if isinstance(boundary, dict):
            if boundary.get('type') == 'Polygon':
                # Extract coordinates from GeoJSON Polygon: coordinates[0] = exterior ring
                coordinates = boundary.get('coordinates', [[]])[0]
            elif boundary.get('type') == 'MultiPolygon':
                # Extract first polygon's exterior ring from MultiPolygon
                coordinates = boundary.get('coordinates', [[[]]])[0][0]
            else:
                logger.error(f"Unknown GeoJSON type: {boundary.get('type')}")
                return False
            
            # GeoJSON coordinates are [lng, lat], convert to polygon format
            polygon = []
            for coord in coordinates:
                if isinstance(coord, list) and len(coord) >= 2:
                    polygon.append({'lat': float(coord[1]), 'lng': float(coord[0])})
        
        # Handle legacy formats (string or array)
        else:
            polygon = []
            coord_list = boundary if isinstance(boundary, list) else []
            
            for coord_str in coord_list:
                if isinstance(coord_str, str) and ',' in coord_str:
                    # Format: "lat,lng"
                    parts = coord_str.split(',')
                    if len(parts) == 2:
                        polygon.append({'lat': float(parts[0].strip()), 'lng': float(parts[1].strip())})
                elif isinstance(coord_str, list) and len(coord_str) == 2:
                    # Format: [lat, lng]
                    polygon.append({'lat': float(coord_str[0]), 'lng': float(coord_str[1])})
        
        if len(polygon) < 3:
            return False
        
        # Ray casting algorithm
        inside = False
        x, y = lng, lat
        
        for i in range(len(polygon)):
            j = (i - 1) % len(polygon)
            xi, yi = polygon[i]['lng'], polygon[i]['lat']
            xj, yj = polygon[j]['lng'], polygon[j]['lat']
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
        
        return inside
    
    except Exception as e:
        logger.error(f"Error in point-in-polygon check: {e}")
        return False


def find_matching_radar_tokens(alert_latitude, alert_longitude, alert_institute_id):
    """
    Find radar tokens that have geofences containing the alert location
    
    Args:
        alert_latitude: Alert latitude coordinate
        alert_longitude: Alert longitude coordinate
        alert_institute_id: Alert's institute ID
    
    Returns:
        list: List of radar tokens that match the alert location
    """
    try:
        # Get all geofences from the same institute
        geofences = AlertGeofence.objects.filter(institute_id=alert_institute_id)
        
        matching_geofence_ids = []
        
        for geofence in geofences:
            if geofence.boundary and is_point_in_polygon(alert_latitude, alert_longitude, geofence.boundary):
                matching_geofence_ids.append(geofence.id)
                logger.info(f"Alert location matches geofence: {geofence.title} (ID: {geofence.id})")
        
        if not matching_geofence_ids:
            logger.info(f"No matching geofences found for alert at ({alert_latitude}, {alert_longitude})")
            return []
        
        # Find radars that contain any of the matching geofences
        matching_radars = AlertRadar.objects.filter(
            institute_id=alert_institute_id,
            alert_geofences__id__in=matching_geofence_ids
        ).distinct()
        
        radar_tokens = [radar.token for radar in matching_radars if radar.token]
        
        logger.info(f"Found {len(radar_tokens)} matching radar tokens: {radar_tokens}")
        return radar_tokens
        
    except Exception as e:
        logger.error(f"Error finding matching radar tokens: {e}")
        return []


def send_alert_notification_via_nodejs(alert_history):
    """
    Send real-time alert notification via Node.js API
    
    Args:
        alert_history: AlertHistory instance
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Find matching radar tokens
        radar_tokens = find_matching_radar_tokens(
            float(alert_history.latitude),
            float(alert_history.longitude),
            alert_history.institute_id
        )
        
        if not radar_tokens:
            logger.info(f"No matching radars found for alert {alert_history.id}")
            return True  # Not an error, just no radars to notify
        
        # Prepare alert data
        alert_data = {
            "id": alert_history.id,
            "institute_id": alert_history.institute_id,
            "name": alert_history.name,
            "primary_phone": alert_history.primary_phone,
            "alert_type_name": alert_history.alert_type.name if alert_history.alert_type else "Unknown",
            "latitude": float(alert_history.latitude),
            "longitude": float(alert_history.longitude),
            "datetime": alert_history.datetime.isoformat(),
            "status": alert_history.status,
            "remarks": alert_history.remarks,
            "source": alert_history.source,
            "image": alert_history.image
        }
        
        # Prepare payload for Node.js API
        payload = {
            "radar_tokens": radar_tokens,
            "alert_data": alert_data
        }
        
        # Send request to Node.js API
        headers = {
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Sending alert notification to Node.js API for alert {alert_history.id}")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            NODEJS_ALERT_NOTIFICATION_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=30  # 30 second timeout
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('success'):
                logger.info(f"Successfully sent alert notification via Node.js API for alert {alert_history.id}")
                logger.info(f"Response: {response_data}")
                return True
            else:
                logger.error(f"Node.js API returned error for alert {alert_history.id}: {response_data}")
                return False
        else:
            logger.error(f"Node.js API request failed for alert {alert_history.id}. Status: {response.status_code}, Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error sending alert notification via Node.js API for alert {alert_history.id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending alert notification via Node.js API for alert {alert_history.id}: {e}")
        return False
