"""
Community Siren SMS Service
Handles SMS notifications for community siren history creation
"""
import logging
import secrets
import string
from typing import List, Dict, Any
from api_common.utils.sms_service import sms_service
from community_siren.models import CommunitySirenHistory, CommunitySirenContact
from django.utils import timezone
from shared.models import ShortLink

logger = logging.getLogger(__name__)


def _build_directions_link(lat: float, lon: float) -> str:
    """Return Google Maps directions URL to destination lat/lon."""
    base = "https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
    return base.format(lat=lat, lon=lon)


_ALPHABET = string.ascii_letters + string.digits


def _generate_code(length: int = 7) -> str:
    return ''.join(secrets.choice(_ALPHABET) for _ in range(length))


def _create_internal_short_link(full_url: str, base: str = "https://mylunago.com", ttl_hours: int = 168) -> str:
    expire_at = timezone.now() + timezone.timedelta(hours=ttl_hours)
    for _ in range(5):
        code = _generate_code()
        try:
            ShortLink.objects.create(code=code, url=full_url, expire_at=expire_at)
            return f"{base}/g/{code}"
        except Exception:
            continue
    return full_url


def find_matching_community_siren_contacts(history: CommunitySirenHistory) -> List[CommunitySirenContact]:
    """
    Find community siren contacts that should receive SMS notifications for this history.
    
    Logic:
    1. Match institute
    2. Filter by is_sms=True
    
    Args:
        history: CommunitySirenHistory instance
        
    Returns:
        List of CommunitySirenContact instances that should be notified
    """
    try:
        # Find contacts that match:
        # - Same institute
        # - is_sms=True
        contacts = CommunitySirenContact.objects.filter(
            institute=history.institute,
            is_sms=True
        ).distinct()
        
        logger.info(f"Found {contacts.count()} matching community siren contacts for history {history.id}")
        return list(contacts)
        
    except Exception as e:
        logger.error(f"Error finding matching community siren contacts for history {history.id}: {e}")
        return []


def send_community_siren_sms_to_contacts(history: CommunitySirenHistory, contacts: List[CommunitySirenContact]) -> Dict[str, Any]:
    """
    Send SMS notifications to community siren contacts.
    
    Args:
        history: CommunitySirenHistory instance
        contacts: List of CommunitySirenContact instances to notify
        
    Returns:
        Dict with success status and details
    """
    try:
        if not contacts:
            logger.info(f"No contacts to notify for community siren history {history.id}")
            return {'success': True, 'message': 'No contacts to notify', 'sent_count': 0}
        
        # Format SMS message with Google Maps directions link (shortened)
        lat = None
        lon = None
        try:
            lat = float(history.latitude) if history.latitude is not None else None
            lon = float(history.longitude) if history.longitude is not None else None
        except (TypeError, ValueError):
            lat = None
            lon = None

        maps_link = None
        if lat is not None and lon is not None:
            full_maps = _build_directions_link(lat, lon)
            maps_link = _create_internal_short_link(full_maps, base="mylunago.com")

        # Build message
        parts = [f"{history.name}, need your help for Community Siren Alert."]
        if maps_link:
            parts.append(maps_link)
        parts.append(f"Contact on {history.primary_phone}.")
        message = " ".join(parts)
        
        sent_count = 0
        failed_count = 0
        results = []
        
        for contact in contacts:
            try:
                sms_result = sms_service.send_sms(contact.phone, message)
                
                if sms_result['success']:
                    sent_count += 1
                    logger.info(f"SMS sent successfully to contact {contact.name} ({contact.phone}) for community siren history {history.id}")
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
        
        logger.info(f"SMS notification completed for community siren history {history.id}: {sent_count} sent, {failed_count} failed")
        
        return {
            'success': True,
            'message': f'SMS notifications sent: {sent_count} successful, {failed_count} failed',
            'sent_count': sent_count,
            'failed_count': failed_count,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error sending community siren SMS to contacts for history {history.id}: {e}")
        return {'success': False, 'message': str(e), 'sent_count': 0, 'failed_count': len(contacts)}


def process_community_siren_sms_notifications(history: CommunitySirenHistory) -> Dict[str, Any]:
    """
    Main function to process all SMS notifications for a new community siren history.
    
    Args:
        history: CommunitySirenHistory instance
        
    Returns:
        Dict with overall success status and details
    """
    try:
        logger.info(f"Processing SMS notifications for community siren history {history.id}")
        
        # Find matching contacts
        contacts = find_matching_community_siren_contacts(history)
        
        # Send SMS to contacts
        contact_result = send_community_siren_sms_to_contacts(history, contacts)
        
        # Overall result
        return {
            'success': contact_result['success'],
            'message': f'SMS notifications processed for community siren history {history.id}',
            'contact_result': contact_result,
            'contacts_found': len(contacts)
        }
        
    except Exception as e:
        logger.error(f"Error processing SMS notifications for community siren history {history.id}: {e}")
        return {
            'success': False,
            'message': str(e),
            'contact_result': {'success': False, 'message': str(e)},
            'contacts_found': 0
        }

