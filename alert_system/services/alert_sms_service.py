"""
Alert SMS Service
Handles SMS notifications for alert creation and updates, including buzzer relay control
"""
import logging
from typing import List, Dict, Any
from django.db.models import Q
from api_common.utils.sms_service import sms_service
from alert_system.models import AlertHistory, AlertContact, AlertBuzzer, AlertGeofence
from alert_system.services.alert_notification_service import is_point_in_polygon

logger = logging.getLogger(__name__)


def _build_directions_link(lat: float, lon: float) -> str:
    """Return Google Maps directions URL to destination lat/lon."""
    base = "https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
    return base.format(lat=lat, lon=lon)


def _shorten_with_tinyurl(url: str) -> str:
    """Shorten a URL using TinyURL API. Falls back to original on error."""
    try:
        from urllib.parse import quote
        from urllib.request import urlopen

        with urlopen("https://tinyurl.com/api-create.php?url=" + quote(url, safe=""), timeout=5) as resp:
            short = resp.read().decode("utf-8").strip()
            return short if short.startswith("http") else url
    except Exception:
        return url


def get_switch_device_phone(alert_history: AlertHistory) -> str:
    """
    Get the device phone number for the alert switch that triggered this alert.
    
    Args:
        alert_history: AlertHistory instance with source='switch'
        
    Returns:
        Device phone number or None
    """
    try:
        from alert_system.models import AlertSwitch
        
        # Find the switch for this alert's institute and phone numbers
        switch = AlertSwitch.objects.filter(
            institute=alert_history.institute,
            primary_phone=alert_history.primary_phone
        ).select_related('device').first()
        
        if switch and switch.device and switch.device.phone:
            return switch.device.phone
        
        logger.warning(f"Could not find switch device for alert {alert_history.id}")
        return None
        
    except Exception as e:
        logger.error(f"Error getting switch device phone for alert {alert_history.id}: {e}")
        return None


def find_matching_alert_contacts(alert_history: AlertHistory) -> List[AlertContact]:
    """
    Find alert contacts that should receive SMS notifications for this alert.
    
    Logic:
    1. Match institute
    2. Find geofences containing the alert location
    3. Find contacts associated with those geofences and alert_types
    4. Filter by is_sms=True
    
    Args:
        alert_history: AlertHistory instance
        
    Returns:
        List of AlertContact instances that should be notified
    """
    try:
        # Get all geofences from the same institute
        institute_geofences = AlertGeofence.objects.filter(institute=alert_history.institute)
        
        # Find geofences containing the alert location
        matching_geofence_ids = []
        for geofence in institute_geofences:
            if geofence.boundary and is_point_in_polygon(
                float(alert_history.latitude), 
                float(alert_history.longitude), 
                geofence.boundary
            ):
                matching_geofence_ids.append(geofence.id)
                logger.info(f"Alert location matches geofence: {geofence.title} (ID: {geofence.id})")
        
        if not matching_geofence_ids:
            logger.info(f"No matching geofences found for alert at ({alert_history.latitude}, {alert_history.longitude})")
            return []
        
        # Find contacts that match:
        # - Same institute
        # - Associated with matching geofences OR no geofences specified (global contacts)
        # - Associated with alert type OR no alert types specified (global contacts)
        # - is_sms=True
        contacts = AlertContact.objects.filter(
            Q(institute=alert_history.institute) &
            Q(is_sms=True) &
            (
                Q(alert_geofences__id__in=matching_geofence_ids) |
                Q(alert_geofences__isnull=True)  # Global contacts (no geofence restriction)
            ) &
            (
                Q(alert_types=alert_history.alert_type) |
                Q(alert_types__isnull=True)  # Global contacts (no alert type restriction)
            )
        ).distinct()
        
        logger.info(f"Found {contacts.count()} matching alert contacts for alert {alert_history.id}")
        return list(contacts)
        
    except Exception as e:
        logger.error(f"Error finding matching alert contacts for alert {alert_history.id}: {e}")
        return []


def find_matching_buzzers(alert_history: AlertHistory) -> List[AlertBuzzer]:
    """
    Find buzzers that should be activated for this alert.
    
    Logic:
    1. Match institute
    2. Find geofences containing the alert location
    3. Find buzzers associated with those geofences
    
    Args:
        alert_history: AlertHistory instance
        
    Returns:
        List of AlertBuzzer instances that should be activated
    """
    try:
        # Get all geofences from the same institute
        institute_geofences = AlertGeofence.objects.filter(institute=alert_history.institute)
        
        # Find geofences containing the alert location
        matching_geofence_ids = []
        for geofence in institute_geofences:
            if geofence.boundary and is_point_in_polygon(
                float(alert_history.latitude), 
                float(alert_history.longitude), 
                geofence.boundary
            ):
                matching_geofence_ids.append(geofence.id)
                logger.info(f"Alert location matches geofence: {geofence.title} (ID: {geofence.id})")
        
        if not matching_geofence_ids:
            logger.info(f"No matching geofences found for alert at ({alert_history.latitude}, {alert_history.longitude})")
            return []
        
        # Find buzzers associated with matching geofences
        buzzers = AlertBuzzer.objects.filter(
            institute=alert_history.institute,
            alert_geofences__id__in=matching_geofence_ids
        ).distinct()
        
        logger.info(f"Found {buzzers.count()} matching buzzers for alert {alert_history.id}")
        return list(buzzers)
        
    except Exception as e:
        logger.error(f"Error finding matching buzzers for alert {alert_history.id}: {e}")
        return []


def send_alert_sms_to_contacts(alert_history: AlertHistory, contacts: List[AlertContact]) -> Dict[str, Any]:
    """
    Send SMS notifications to alert contacts.
    
    Args:
        alert_history: AlertHistory instance
        contacts: List of AlertContact instances to notify
        
    Returns:
        Dict with success status and details
    """
    try:
        if not contacts:
            logger.info(f"No contacts to notify for alert {alert_history.id}")
            return {'success': True, 'message': 'No contacts to notify', 'sent_count': 0}
        
        # Format SMS message with Google Maps directions link (shortened)
        alert_type_name = alert_history.alert_type.name if alert_history.alert_type else "Unknown"

        lat = None
        lon = None
        try:
            lat = float(alert_history.latitude) if alert_history.latitude is not None else None
            lon = float(alert_history.longitude) if alert_history.longitude is not None else None
        except (TypeError, ValueError):
            lat = None
            lon = None

        maps_link = None
        if lat is not None and lon is not None:
            try:
                maps_link = _shorten_with_tinyurl(_build_directions_link(lat, lon))
            except Exception:
                maps_link = _build_directions_link(lat, lon)

        parts = [f"{alert_history.name}, need your help for {alert_type_name}."]
        if maps_link:
            parts.append(maps_link)
        parts.append("https://www.mylunago.com")
        parts.append(f"Contact on {alert_history.primary_phone}.")
        message = " ".join(parts)
        
        sent_count = 0
        failed_count = 0
        results = []
        
        for contact in contacts:
            try:
                sms_result = sms_service.send_sms(contact.phone, message)
                
                if sms_result['success']:
                    sent_count += 1
                    logger.info(f"SMS sent successfully to contact {contact.name} ({contact.phone}) for alert {alert_history.id}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to send SMS to contact {contact.name} ({contact.phone}): {sms_result['message']}")
                
                results.append({
                    'contact_id': contact.id,
                    'contact_name': contact.name,
                    'phone': contact.phone,
                    'success': sms_result['success'],
                    'message': sms_result['message']
                })
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Error sending SMS to contact {contact.name} ({contact.phone}): {e}")
                results.append({
                    'contact_id': contact.id,
                    'contact_name': contact.name,
                    'phone': contact.phone,
                    'success': False,
                    'message': str(e)
                })
        
        logger.info(f"SMS notification completed for alert {alert_history.id}: {sent_count} sent, {failed_count} failed")
        
        return {
            'success': True,
            'message': f'SMS notifications sent: {sent_count} successful, {failed_count} failed',
            'sent_count': sent_count,
            'failed_count': failed_count,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error sending alert SMS to contacts for alert {alert_history.id}: {e}")
        return {'success': False, 'message': str(e), 'sent_count': 0, 'failed_count': len(contacts)}


def send_buzzer_relay_commands(alert_history: AlertHistory, buzzers: List[AlertBuzzer]) -> Dict[str, Any]:
    """
    Send relay ON commands to buzzers and schedule relay OFF commands.
    If alert source is 'switch', also send relay to the switch device.
    
    Args:
        alert_history: AlertHistory instance
        buzzers: List of AlertBuzzer instances to activate
        
    Returns:
        Dict with success status and details
    """
    try:
        if not buzzers:
            logger.info(f"No buzzers to activate for alert {alert_history.id}")
            return {'success': True, 'message': 'No buzzers to activate', 'activated_count': 0}
        
        activated_count = 0
        failed_count = 0
        results = []
        
        for buzzer in buzzers:
            try:
                # Send relay ON command to buzzer
                relay_on_result = sms_service.send_relay_on_command(buzzer.device.phone)
                
                if relay_on_result['success']:
                    activated_count += 1
                    logger.info(f"Relay ON sent to buzzer {buzzer.title} ({buzzer.device.phone})")
                    
                    # Schedule relay OFF for buzzer
                    from alert_system.tasks import schedule_relay_off_command
                    schedule_relay_off_command(
                        buzzer.device.phone,
                        buzzer.delay,
                        alert_history.id,
                        buzzer.id
                    )
                    
                    # If source is 'switch', also send relay to switch device
                    if alert_history.source == 'switch':
                        switch_device_phone = get_switch_device_phone(alert_history)
                        
                        if switch_device_phone:
                            switch_relay_result = sms_service.send_relay_on_command(switch_device_phone)
                            
                            if switch_relay_result['success']:
                                logger.info(f"Relay ON sent to switch device ({switch_device_phone})")
                                
                                # Schedule relay OFF for switch device (same delay as buzzer)
                                schedule_relay_off_command(
                                    switch_device_phone,
                                    buzzer.delay,
                                    alert_history.id,
                                    buzzer.id
                                )
                            else:
                                logger.warning(f"Failed to send relay ON to switch device ({switch_device_phone})")
                    
                else:
                    failed_count += 1
                    logger.warning(f"Failed to send relay ON to buzzer {buzzer.title}")
                
                results.append({
                    'buzzer_id': buzzer.id,
                    'buzzer_title': buzzer.title,
                    'device_phone': buzzer.device.phone,
                    'delay': buzzer.delay,
                    'success': relay_on_result['success'],
                    'message': relay_on_result['message']
                })
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Error activating buzzer {buzzer.title}: {e}")
        
        return {
            'success': True,
            'message': f'Buzzer activation completed: {activated_count} activated, {failed_count} failed',
            'activated_count': activated_count,
            'failed_count': failed_count,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error activating buzzers for alert {alert_history.id}: {e}")
        return {'success': False, 'message': str(e)}


def send_alert_acceptance_sms(alert_history: AlertHistory) -> Dict[str, Any]:
    """
    Send acceptance SMS to the alert sender when status or remarks are updated.
    
    Args:
        alert_history: AlertHistory instance
        
    Returns:
        Dict with success status and details
    """
    try:
        # Format SMS message
        institute_name = alert_history.institute.name if alert_history.institute else "Unknown Institute"
        alert_type_name = alert_history.alert_type.name if alert_history.alert_type else "Unknown"
        message = f"{institute_name} accepted help for your {alert_type_name}"
        
        # Send SMS to primary phone
        sms_result = sms_service.send_sms(alert_history.primary_phone, message)
        
        if sms_result['success']:
            logger.info(f"Acceptance SMS sent successfully to {alert_history.primary_phone} for alert {alert_history.id}")
            return {
                'success': True,
                'message': 'Acceptance SMS sent successfully',
                'phone': alert_history.primary_phone,
                'institute_name': institute_name
            }
        else:
            logger.warning(f"Failed to send acceptance SMS to {alert_history.primary_phone}: {sms_result['message']}")
            return {
                'success': False,
                'message': f"Failed to send acceptance SMS: {sms_result['message']}",
                'phone': alert_history.primary_phone,
                'institute_name': institute_name
            }
            
    except Exception as e:
        logger.error(f"Error sending acceptance SMS for alert {alert_history.id}: {e}")
        return {
            'success': False,
            'message': str(e),
            'phone': alert_history.primary_phone,
            'institute_name': institute_name if alert_history.institute else "Unknown Institute"
        }


def process_alert_sms_notifications(alert_history: AlertHistory) -> Dict[str, Any]:
    """
    Main function to process all SMS notifications for a new alert.
    
    Args:
        alert_history: AlertHistory instance
        
    Returns:
        Dict with overall success status and details
    """
    try:
        logger.info(f"Processing SMS notifications for alert {alert_history.id}")
        
        # Find matching contacts and buzzers
        contacts = find_matching_alert_contacts(alert_history)
        buzzers = find_matching_buzzers(alert_history)
        
        # Send SMS to contacts
        contact_result = send_alert_sms_to_contacts(alert_history, contacts)
        
        # Send relay commands to buzzers
        buzzer_result = send_buzzer_relay_commands(alert_history, buzzers)
        
        # Overall result
        overall_success = contact_result['success'] and buzzer_result['success']
        
        return {
            'success': overall_success,
            'message': f'SMS notifications processed for alert {alert_history.id}',
            'contact_result': contact_result,
            'buzzer_result': buzzer_result,
            'contacts_found': len(contacts),
            'buzzers_found': len(buzzers)
        }
        
    except Exception as e:
        logger.error(f"Error processing SMS notifications for alert {alert_history.id}: {e}")
        return {
            'success': False,
            'message': str(e),
            'contact_result': {'success': False, 'message': str(e)},
            'buzzer_result': {'success': False, 'message': str(e)},
            'contacts_found': 0,
            'buzzers_found': 0
        }