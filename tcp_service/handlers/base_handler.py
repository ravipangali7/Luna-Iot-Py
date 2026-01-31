"""
Base Handler for JT808 Messages

Provides common functionality for all message handlers.
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """Abstract base class for JT808 message handlers."""
    
    def __init__(self, device_manager=None):
        """
        Initialize handler with optional device manager.
        
        Args:
            device_manager: DeviceManager instance for tracking connections
        """
        self.device_manager = device_manager
    
    @abstractmethod
    async def handle(self, message: Dict[str, Any], writer=None) -> Optional[bytes]:
        """
        Handle a parsed JT808 message.
        
        Args:
            message: Parsed message dict from jt808_parser.parse_message()
            writer: asyncio.StreamWriter for sending responses
        
        Returns:
            Response bytes to send, or None if no response needed
        """
        pass
    
    def get_nepal_datetime(self, dt: datetime = None) -> datetime:
        """
        Convert datetime to Nepal timezone (UTC+5:45).
        
        Args:
            dt: datetime to convert, or None for current time
        
        Returns:
            datetime in Nepal timezone
        """
        from datetime import timedelta
        
        if dt is None:
            dt = datetime.utcnow()
        
        # Nepal is UTC+5:45
        nepal_offset = timedelta(hours=5, minutes=45)
        return dt + nepal_offset
    
    def log_message(self, msg_type: str, phone: str, details: str = ""):
        """Log a message event."""
        logger.info(f"[{msg_type}] Phone: {phone} {details}")
