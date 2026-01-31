"""
Device Manager

Manages connected dashcam devices and their states.
Tracks connections, video buffers, and sequence numbers.
"""
import logging
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    """Information about a connected device."""
    device_id: str
    phone: str
    auth_code: str = ""
    manufacturer: str = ""
    model: str = ""
    connected_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    location: Dict[str, float] = field(default_factory=dict)
    channels: list = field(default_factory=list)
    is_streaming: bool = False
    stream_channel: int = 0


class DeviceManager:
    """
    Manages connected dashcam devices.
    
    Tracks:
    - Device information and connection state
    - TCP writers for sending commands
    - Video buffers for streaming
    - Sequence numbers for protocol messages
    - WebSocket clients for video streaming
    """
    
    def __init__(self):
        self.devices: Dict[str, DeviceInfo] = {}
        self.connections: Dict[str, asyncio.StreamWriter] = {}
        self.video_connections: Dict[str, asyncio.StreamWriter] = {}
        self.seq_numbers: Dict[str, int] = {}
        self.websocket_clients: Dict[str, set] = {}  # phone -> set of websocket consumers
        self._lock = asyncio.Lock()
    
    def register_device(self, phone: str, auth_code: str = "", writer=None) -> DeviceInfo:
        """
        Register a new device or update existing.
        
        Args:
            phone: Device phone/SIM number (used as ID)
            auth_code: Authentication code
            writer: asyncio.StreamWriter for the connection
        
        Returns:
            DeviceInfo object
        """
        if phone in self.devices:
            # Update existing device
            device = self.devices[phone]
            device.auth_code = auth_code or device.auth_code
            device.last_heartbeat = datetime.now()
        else:
            # Create new device entry
            device = DeviceInfo(
                device_id=phone,
                phone=phone,
                auth_code=auth_code,
                connected_at=datetime.now(),
                last_heartbeat=datetime.now()
            )
            self.devices[phone] = device
            self.seq_numbers[phone] = 0
        
        if writer:
            self.connections[phone] = writer
        
        logger.info(f"[DeviceManager] Registered device: {phone}")
        return device
    
    def get_device(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get device info as dict."""
        device = self.devices.get(phone)
        if device:
            return {
                'device_id': device.device_id,
                'phone': device.phone,
                'auth_code': device.auth_code,
                'connected_at': device.connected_at,
                'last_heartbeat': device.last_heartbeat,
                'location': device.location,
                'is_streaming': device.is_streaming,
                'stream_channel': device.stream_channel,
            }
        return None
    
    def set_connection(self, phone: str, writer: asyncio.StreamWriter):
        """Set the TCP connection writer for a device."""
        self.connections[phone] = writer
    
    def get_connection(self, phone: str) -> Optional[asyncio.StreamWriter]:
        """Get the TCP connection writer for a device."""
        return self.connections.get(phone)
    
    def set_video_connection(self, phone: str, writer: asyncio.StreamWriter):
        """Set the video stream connection writer for a device."""
        self.video_connections[phone] = writer
    
    def get_video_connection(self, phone: str) -> Optional[asyncio.StreamWriter]:
        """Get the video stream connection writer for a device."""
        return self.video_connections.get(phone)
    
    def remove_device(self, phone: str):
        """Remove a device from tracking."""
        self.devices.pop(phone, None)
        self.connections.pop(phone, None)
        self.video_connections.pop(phone, None)
        self.seq_numbers.pop(phone, None)
        self.websocket_clients.pop(phone, None)
        logger.info(f"[DeviceManager] Removed device: {phone}")
    
    def get_next_seq(self, phone: str) -> int:
        """Get and increment sequence number for a device."""
        seq = self.seq_numbers.get(phone, 0)
        self.seq_numbers[phone] = (seq + 1) % 65536
        return seq
    
    def set_streaming(self, phone: str, is_streaming: bool, channel: int = 0):
        """Update streaming status for a device."""
        if phone in self.devices:
            self.devices[phone].is_streaming = is_streaming
            self.devices[phone].stream_channel = channel if is_streaming else 0
    
    def add_websocket_client(self, phone: str, client):
        """Add a WebSocket client for video streaming."""
        if phone not in self.websocket_clients:
            self.websocket_clients[phone] = set()
        self.websocket_clients[phone].add(client)
        logger.debug(f"[DeviceManager] Added WebSocket client for {phone}")
    
    def remove_websocket_client(self, phone: str, client):
        """Remove a WebSocket client."""
        if phone in self.websocket_clients:
            self.websocket_clients[phone].discard(client)
            if not self.websocket_clients[phone]:
                del self.websocket_clients[phone]
    
    def get_websocket_clients(self, phone: str) -> set:
        """Get all WebSocket clients for a device."""
        return self.websocket_clients.get(phone, set())
    
    async def broadcast_video(self, phone: str, data: bytes, is_init: bool = False, 
                               codec: str = None, channel: int = 1):
        """
        Broadcast video data to all WebSocket clients for a device.
        
        Args:
            phone: Device phone/SIM number
            data: Video data (fMP4 segment)
            is_init: True if this is an init segment
            codec: Codec string (only for init segment)
            channel: Camera channel (1=Front, 2=Rear)
        """
        clients = self.get_websocket_clients(phone)
        if not clients:
            return
        
        import base64
        data_b64 = base64.b64encode(data).decode('utf-8')
        
        message = {
            'type': 'init_segment' if is_init else 'video',
            'phone': phone,
            'channel': channel,
            'data': data_b64,
        }
        
        if is_init and codec:
            message['codec'] = codec
        
        # Broadcast to all clients
        disconnected = []
        for client in clients:
            try:
                await client.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(client)
        
        # Clean up disconnected clients
        for client in disconnected:
            self.remove_websocket_client(phone, client)
    
    def get_all_devices(self) -> list:
        """Get list of all connected devices."""
        return [
            {
                'phone': d.phone,
                'device_id': d.device_id,
                'connected_at': d.connected_at.isoformat(),
                'last_heartbeat': d.last_heartbeat.isoformat(),
                'is_streaming': d.is_streaming,
                'stream_channel': d.stream_channel,
            }
            for d in self.devices.values()
        ]
    
    def get_connected_count(self) -> int:
        """Get number of connected devices."""
        return len(self.devices)


# Global device manager instance
device_manager = DeviceManager()
