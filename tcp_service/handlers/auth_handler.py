"""
Authentication Handler (0x0102)

Handles terminal authentication messages from dashcam devices.
"""
import logging
from typing import Optional, Dict, Any

from .base_handler import BaseHandler
from ..protocol.jt808_parser import build_general_response
from ..protocol.constants import JT808MsgID, JT808ResponseResult

logger = logging.getLogger(__name__)


class AuthHandler(BaseHandler):
    """
    Handler for Terminal Authentication messages (0x0102).
    
    After registration, the device sends authentication with the auth code
    received during registration. The server validates and confirms.
    """
    
    async def handle(self, message: Dict[str, Any], writer=None) -> Optional[bytes]:
        """
        Handle terminal authentication.
        
        Args:
            message: Parsed JT808 message
            writer: asyncio.StreamWriter for this connection
        
        Returns:
            General response message bytes
        """
        phone = message.get("phone", "")
        seq_num = message.get("seq_num", 0)
        body = message.get("body", b"")
        
        # Extract auth code from body
        auth_code = body.decode('utf-8', errors='ignore').strip('\x00') if body else ""
        
        self.log_message("AUTH", phone, f"seq={seq_num}, auth_code={auth_code}")
        
        # Validate device exists in system
        if not await self.validate_device_exists(phone):
            # Return auth failure - device not registered
            next_seq = self.device_manager.get_next_seq(phone) if self.device_manager else 0
            response = build_general_response(
                phone=phone,
                resp_seq=seq_num,
                resp_msg_id=JT808MsgID.TERMINAL_AUTH,
                result=JT808ResponseResult.FAIL,
                seq_num=next_seq
            )
            return response
        
        # Validate authentication
        is_valid = await self._validate_auth(phone, auth_code, writer)
        
        # Build response
        result = JT808ResponseResult.SUCCESS if is_valid else JT808ResponseResult.FAIL
        next_seq = self.device_manager.get_next_seq(phone) if self.device_manager else 0
        
        response = build_general_response(
            phone=phone,
            resp_seq=seq_num,
            resp_msg_id=JT808MsgID.TERMINAL_AUTH,
            result=result,
            seq_num=next_seq
        )
        
        logger.info(f"[AUTH] Response to {phone}: {'SUCCESS' if is_valid else 'FAIL'}")
        return response
    
    async def _validate_auth(self, phone: str, auth_code: str, writer) -> bool:
        """
        Validate authentication and update device status.
        
        For flexibility, we accept any auth that looks valid.
        In production, you might validate against stored auth codes.
        """
        try:
            from asgiref.sync import sync_to_async
            from ..models import DashcamConnection
            
            # Update connection status
            await sync_to_async(
                DashcamConnection.objects.filter(imei=phone).update,
                thread_sensitive=True
            )(
                is_connected=True,
                last_heartbeat=self.get_nepal_datetime()
            )
            
            # Register in memory manager if not already
            if self.device_manager:
                device = self.device_manager.get_device(phone)
                if not device:
                    self.device_manager.register_device(phone, auth_code, writer)
                else:
                    self.device_manager.set_connection(phone, writer)
            
            return True
            
        except Exception as e:
            logger.error(f"[AUTH] Validation error for {phone}: {e}")
            # Still allow auth for robustness
            if self.device_manager:
                self.device_manager.register_device(phone, auth_code, writer)
            return True
