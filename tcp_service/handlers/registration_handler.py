"""
Registration Handler (0x0100)

Handles terminal registration messages from dashcam devices.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .base_handler import BaseHandler
from ..protocol.jt808_parser import (
    parse_registration,
    build_registration_response,
)
from ..protocol.constants import JT808MsgID, JT808RegistrationResult

logger = logging.getLogger(__name__)


class RegistrationHandler(BaseHandler):
    """
    Handler for Terminal Registration messages (0x0100).
    
    When a dashcam first connects, it sends a registration request.
    The server responds with an authentication code that the device
    uses for subsequent authentication.
    """
    
    async def handle(self, message: Dict[str, Any], writer=None) -> Optional[bytes]:
        """
        Handle terminal registration.
        
        Args:
            message: Parsed JT808 message
            writer: asyncio.StreamWriter for this connection
        
        Returns:
            Registration response message bytes
        """
        phone = message.get("phone", "")
        seq_num = message.get("seq_num", 0)
        body = message.get("body", b"")
        
        self.log_message("REGISTRATION", phone, f"seq={seq_num}")
        
        # Validate device exists in system
        if not await self.validate_device_exists(phone):
            # Return registration failure - device not registered
            next_seq = self.device_manager.get_next_seq(phone) if self.device_manager else 0
            response = build_registration_response(
                phone=phone,
                resp_seq=seq_num,
                result=JT808RegistrationResult.NO_TERMINAL,
                auth_code="",
                seq_num=next_seq
            )
            return response
        
        # Parse registration details
        reg_data = parse_registration(body)
        if reg_data:
            logger.info(f"Registration data: manufacturer={reg_data.get('manufacturer')}, "
                       f"model={reg_data.get('terminal_model')}, "
                       f"terminal_id={reg_data.get('terminal_id')}")
        
        # Generate auth code
        auth_code = self._generate_auth_code(phone)
        
        # Register device in manager if available
        if self.device_manager:
            await self._register_device(phone, auth_code, reg_data, writer)
        
        # Build and return response
        result = JT808RegistrationResult.SUCCESS
        next_seq = self.device_manager.get_next_seq(phone) if self.device_manager else 0
        
        response = build_registration_response(
            phone=phone,
            resp_seq=seq_num,
            result=result,
            auth_code=auth_code,
            seq_num=next_seq
        )
        
        logger.info(f"[REGISTRATION] Sent response to {phone}: auth_code={auth_code}")
        return response
    
    def _generate_auth_code(self, phone: str) -> str:
        """Generate a unique auth code for the device."""
        # Simple auth code based on phone and timestamp
        timestamp = datetime.now().strftime("%H%M%S")
        return f"AUTH{phone[-4:]}{timestamp}"
    
    async def _register_device(self, phone: str, auth_code: str, 
                                reg_data: Optional[Dict], writer) -> None:
        """Register device in device manager."""
        try:
            from asgiref.sync import sync_to_async
            from ..models import DashcamConnection
            
            # Extract IMEI and other data from registration
            imei = reg_data.get('terminal_id', '') if reg_data else ''
            manufacturer = reg_data.get('manufacturer', '') if reg_data else ''
            terminal_model = reg_data.get('terminal_model', '') if reg_data else ''
            
            # Use IMEI as the primary identifier if available, otherwise use phone
            device_identifier = imei if imei else phone
            
            # Get or create connection record
            connection, created = await sync_to_async(
                DashcamConnection.objects.update_or_create,
                thread_sensitive=True
            )(
                imei=device_identifier,
                defaults={
                    'phone': phone,
                    'auth_code': auth_code,
                    'is_connected': True,
                    'connected_at': self.get_nepal_datetime(),
                    'last_heartbeat': self.get_nepal_datetime(),
                }
            )
            
            # Register in memory manager with all registration data
            if self.device_manager:
                self.device_manager.register_device(
                    phone=phone,
                    auth_code=auth_code,
                    writer=writer,
                    imei=imei,
                    manufacturer=manufacturer,
                    terminal_model=terminal_model
                )
            
            action = "Created" if created else "Updated"
            logger.info(f"[REGISTRATION] {action} connection record: phone={phone}, imei={imei}, manufacturer={manufacturer}, model={terminal_model}")
            
        except Exception as e:
            logger.error(f"[REGISTRATION] Failed to register device {phone}: {e}")
