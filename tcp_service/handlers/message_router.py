"""
Message Router

Routes incoming JT808 messages to appropriate handlers based on message ID.
"""
import logging
from typing import Optional, Dict, Any

from .registration_handler import RegistrationHandler
from .auth_handler import AuthHandler
from .heartbeat_handler import HeartbeatHandler
from .location_handler import LocationHandler
from ..protocol.constants import JT808MsgID
from ..protocol.jt808_parser import build_general_response

logger = logging.getLogger(__name__)


class MessageRouter:
    """
    Routes JT808 messages to appropriate handlers.
    
    Maintains a registry of handlers for different message types
    and dispatches incoming messages accordingly.
    """
    
    def __init__(self, device_manager=None):
        """
        Initialize router with handlers.
        
        Args:
            device_manager: DeviceManager instance for tracking connections
        """
        self.device_manager = device_manager
        
        # Initialize handlers
        self.handlers = {
            JT808MsgID.TERMINAL_REGISTRATION: RegistrationHandler(device_manager),
            JT808MsgID.TERMINAL_AUTH: AuthHandler(device_manager),
            JT808MsgID.TERMINAL_HEARTBEAT: HeartbeatHandler(device_manager),
            JT808MsgID.LOCATION_REPORT: LocationHandler(device_manager),
        }
        
        # Message IDs that don't need a response
        self.no_response_messages = {
            JT808MsgID.TERMINAL_GENERAL_RESPONSE,
        }
    
    async def route(self, message: Dict[str, Any], writer=None) -> Optional[bytes]:
        """
        Route a message to appropriate handler.
        
        Args:
            message: Parsed JT808 message dict
            writer: asyncio.StreamWriter for this connection
        
        Returns:
            Response bytes or None
        """
        msg_id = message.get("msg_id")
        phone = message.get("phone", "unknown")
        
        if msg_id is None:
            logger.warning(f"Message with no ID from {phone}")
            return None
        
        # Check if this is a response that doesn't need handling
        if msg_id in self.no_response_messages:
            logger.debug(f"Received response message 0x{msg_id:04X} from {phone}")
            return None
        
        # Find handler
        handler = self.handlers.get(msg_id)
        
        if handler:
            try:
                return await handler.handle(message, writer)
            except Exception as e:
                logger.error(f"Handler error for 0x{msg_id:04X} from {phone}: {e}")
                # Return generic success response on error
                return self._build_default_response(message)
        else:
            # Unknown message - return generic acknowledgment
            logger.info(f"Unknown message 0x{msg_id:04X} from {phone}")
            return self._build_default_response(message)
    
    def _build_default_response(self, message: Dict[str, Any]) -> bytes:
        """Build a default success response for unhandled messages."""
        phone = message.get("phone", "")
        seq_num = message.get("seq_num", 0)
        msg_id = message.get("msg_id", 0)
        
        next_seq = 0
        if self.device_manager:
            next_seq = self.device_manager.get_next_seq(phone)
        
        return build_general_response(
            phone=phone,
            resp_seq=seq_num,
            resp_msg_id=msg_id,
            result=0,  # Success
            seq_num=next_seq
        )
    
    def register_handler(self, msg_id: int, handler):
        """Register a custom handler for a message type."""
        self.handlers[msg_id] = handler
    
    def unregister_handler(self, msg_id: int):
        """Remove handler for a message type."""
        if msg_id in self.handlers:
            del self.handlers[msg_id]
