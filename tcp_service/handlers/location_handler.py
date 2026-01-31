"""
Location Handler (0x0200)

Handles location report messages from dashcam devices.
Implements deduplication logic: only insert if data changed, otherwise update timestamp.
"""
import logging
from typing import Optional, Dict, Any

from .base_handler import BaseHandler
from ..protocol.jt808_parser import build_general_response, parse_location_report
from ..protocol.constants import JT808MsgID, JT808ResponseResult

logger = logging.getLogger(__name__)


class LocationHandler(BaseHandler):
    """
    Handler for Location Report messages (0x0200).
    
    Devices send location reports periodically or on specific events.
    This handler implements deduplication logic similar to the Node.js GT06 handler:
    - If location data changed: INSERT new record
    - If location data same: UPDATE only updated_at timestamp
    """
    
    async def handle(self, message: Dict[str, Any], writer=None) -> Optional[bytes]:
        """
        Handle location report.
        
        Args:
            message: Parsed JT808 message
            writer: asyncio.StreamWriter for this connection
        
        Returns:
            General response message bytes
        """
        phone = message.get("phone", "")
        seq_num = message.get("seq_num", 0)
        body = message.get("body", b"")
        
        # Validate device exists in system
        if not await self.validate_device_exists(phone):
            # Silently ignore unregistered device data
            return None
        
        # Parse location data
        location_data = parse_location_report(body)
        
        if location_data:
            # Save location with deduplication
            await self._save_location(phone, location_data)
            
            # Trigger notification services (non-blocking)
            await self._trigger_notifications(phone, location_data)
        else:
            logger.warning(f"[LOCATION] Failed to parse location for {phone}")
        
        # Build response
        next_seq = self.device_manager.get_next_seq(phone) if self.device_manager else 0
        
        response = build_general_response(
            phone=phone,
            resp_seq=seq_num,
            resp_msg_id=JT808MsgID.LOCATION_REPORT,
            result=JT808ResponseResult.SUCCESS,
            seq_num=next_seq
        )
        
        return response
    
    async def _save_location(self, phone: str, location_data: Dict[str, Any]) -> None:
        """
        Save location data with deduplication.
        
        Following the Node.js GT06 handler pattern:
        - Fetch latest location from database
        - Compare all fields
        - If different: INSERT new record
        - If same: UPDATE only updated_at timestamp
        """
        try:
            from asgiref.sync import sync_to_async
            from ..models import DashcamLocation
            
            nepal_time = self.get_nepal_datetime()
            
            # Fetch latest location for comparison
            latest = await sync_to_async(
                lambda: DashcamLocation.objects.filter(imei=phone).order_by('-created_at').first(),
                thread_sensitive=True
            )()
            
            # Prepare new location data
            new_data = {
                'latitude': location_data['latitude'],
                'longitude': location_data['longitude'],
                'altitude': location_data['altitude'],
                'speed': location_data['speed'],
                'direction': location_data['direction'],
                'alarm_flags': location_data['alarm_flags'],
                'status_flags': location_data['status_flags'],
            }
            
            # Check if data changed (deduplication)
            should_insert = True
            if latest:
                should_insert = not self._locations_equal(latest, new_data)
            
            if should_insert:
                # Data changed - insert new record
                await sync_to_async(
                    DashcamLocation.objects.create,
                    thread_sensitive=True
                )(
                    imei=phone,
                    **new_data
                )
                logger.debug(f"[LOCATION] Inserted new location for {phone}")
            else:
                # Data same - update timestamp only
                await sync_to_async(
                    lambda: DashcamLocation.objects.filter(id=latest.id).update(updated_at=nepal_time),
                    thread_sensitive=True
                )()
                logger.debug(f"[LOCATION] Updated timestamp for {phone}")
            
            # Update device manager with current location
            if self.device_manager:
                device = self.device_manager.get_device(phone)
                if device:
                    device['location'] = new_data
                    device['last_location_time'] = nepal_time
            
        except Exception as e:
            logger.error(f"[LOCATION] Failed to save for {phone}: {e}")
    
    def _locations_equal(self, latest, new_data: Dict) -> bool:
        """Check if two locations are equal (for deduplication)."""
        try:
            return (
                abs(float(latest.latitude) - float(new_data['latitude'])) < 0.000001 and
                abs(float(latest.longitude) - float(new_data['longitude'])) < 0.000001 and
                abs(float(latest.speed) - float(new_data['speed'])) < 0.1 and
                int(latest.direction) == int(new_data['direction']) and
                int(latest.altitude) == int(new_data['altitude'])
            )
        except Exception:
            return False
    
    async def _trigger_notifications(self, phone: str, location_data: Dict[str, Any]) -> None:
        """
        Trigger notification services (non-blocking).
        
        This includes:
        - Geofence checking
        - Speed limit checking
        - School bus proximity
        - Public vehicle proximity
        - Garbage vehicle proximity
        """
        try:
            from ..services import notification_dispatcher
            
            # Fire-and-forget notification dispatch
            await notification_dispatcher.dispatch_location_notifications(
                imei=phone,
                latitude=location_data['latitude'],
                longitude=location_data['longitude'],
                speed=location_data['speed'],
                alarm_flags=location_data['alarm_flags']
            )
        except ImportError:
            # Notification services not yet implemented
            pass
        except Exception as e:
            logger.error(f"[LOCATION] Notification dispatch error for {phone}: {e}")
