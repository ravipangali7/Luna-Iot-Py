"""
Heartbeat Handler (0x0002)

Handles terminal heartbeat messages from dashcam devices.
"""
import logging
from typing import Optional, Dict, Any

from .base_handler import BaseHandler
from ..protocol.jt808_parser import build_general_response
from ..protocol.constants import JT808MsgID, JT808ResponseResult

logger = logging.getLogger(__name__)


class HeartbeatHandler(BaseHandler):
    """
    Handler for Terminal Heartbeat messages (0x0002).
    
    Devices send heartbeat messages periodically (typically every 30-60 seconds)
    to maintain the connection and indicate they are still active.
    """
    
    async def handle(self, message: Dict[str, Any], writer=None) -> Optional[bytes]:
        """
        Handle terminal heartbeat.
        
        Args:
            message: Parsed JT808 message
            writer: asyncio.StreamWriter for this connection
        
        Returns:
            General response message bytes
        """
        phone = message.get("phone", "")
        seq_num = message.get("seq_num", 0)
        
        # Validate device exists in system
        if not await self.validate_device_exists(phone):
            # Silently ignore unregistered device heartbeat
            return None
        
        # Update last heartbeat time
        await self._update_heartbeat(phone)
        
        # Build response
        next_seq = self.device_manager.get_next_seq(phone) if self.device_manager else 0
        
        response = build_general_response(
            phone=phone,
            resp_seq=seq_num,
            resp_msg_id=JT808MsgID.TERMINAL_HEARTBEAT,
            result=JT808ResponseResult.SUCCESS,
            seq_num=next_seq
        )
        
        return response
    
    async def _update_heartbeat(self, phone: str) -> None:
        """Update last heartbeat timestamp for the device."""
        try:
            from asgiref.sync import sync_to_async
            from ..models import DashcamConnection
            
            # Update in database
            await sync_to_async(
                DashcamConnection.objects.filter(imei=phone).update,
                thread_sensitive=True
            )(
                last_heartbeat=self.get_nepal_datetime(),
                is_connected=True
            )
            
            # Update in memory manager
            if self.device_manager:
                device = self.device_manager.get_device(phone)
                if device:
                    device['last_heartbeat'] = self.get_nepal_datetime()
            
        except Exception as e:
            logger.error(f"[HEARTBEAT] Failed to update for {phone}: {e}")
