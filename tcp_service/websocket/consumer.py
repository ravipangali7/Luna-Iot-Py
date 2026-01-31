"""
Django Channels WebSocket Consumer for Dashcam Video Streaming

Handles WebSocket connections from browser clients for live video streaming.
"""
import json
import logging
from typing import Optional
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from ..tcp.device_manager import device_manager
from ..protocol.jt808_parser import build_realtime_av_request, build_av_control
from ..protocol.constants import JT808MsgID

logger = logging.getLogger(__name__)


class DashcamVideoConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for dashcam video streaming.
    
    Handles:
    - Client connection/disconnection
    - Start/stop live stream commands
    - Video data forwarding from TCP server
    - Device list queries
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscribed_devices = set()
        self.current_phone = None
    
    async def connect(self):
        """Handle WebSocket connection."""
        # Accept the connection
        await self.accept()
        logger.info(f"[WebSocket] Client connected")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Unsubscribe from all devices
        for phone in self.subscribed_devices:
            device_manager.remove_websocket_client(phone, self)
        
        logger.info(f"[WebSocket] Client disconnected (code={close_code})")
    
    async def receive_json(self, content):
        """
        Handle incoming JSON messages from client.
        
        Supported actions:
        - get_devices: List connected devices
        - start_live: Start live video stream
        - stop_live: Stop live video stream
        """
        action = content.get('action')
        
        try:
            if action == 'get_devices':
                await self._handle_get_devices()
            
            elif action == 'start_live':
                await self._handle_start_live(content)
            
            elif action == 'stop_live':
                await self._handle_stop_live(content)
            
            else:
                await self.send_json({
                    'type': 'error',
                    'message': f'Unknown action: {action}'
                })
        
        except Exception as e:
            logger.error(f"[WebSocket] Error handling action {action}: {e}")
            await self.send_json({
                'type': 'error',
                'message': str(e)
            })
    
    async def _handle_get_devices(self):
        """Handle get_devices action."""
        devices = device_manager.get_all_devices()
        await self.send_json({
            'type': 'devices',
            'devices': devices
        })
    
    async def _handle_start_live(self, content):
        """
        Handle start_live action.
        
        Args:
            content: {
                'action': 'start_live',
                'phone': '123456789012',
                'channel': 1,  # 1=Front, 2=Rear
                'stream_type': 0  # 0=Main (HD), 1=Sub (SD)
            }
        """
        phone = content.get('phone')
        channel = content.get('channel', 1)
        stream_type = content.get('stream_type', 0)
        
        if not phone:
            await self.send_json({
                'type': 'error',
                'message': 'Phone number required'
            })
            return
        
        # Check if device is connected
        device = device_manager.get_device(phone)
        if not device:
            await self.send_json({
                'type': 'error',
                'message': 'Device not connected'
            })
            return
        
        # Subscribe to video updates
        device_manager.add_websocket_client(phone, self)
        self.subscribed_devices.add(phone)
        self.current_phone = phone
        
        # Send stream request to device
        success = await self._send_stream_request(phone, channel, stream_type)
        
        # Update streaming status
        device_manager.set_streaming(phone, True, channel)
        
        await self.send_json({
            'type': 'response',
            'action': 'start_live',
            'success': success,
            'phone': phone,
            'channel': channel
        })
        
        logger.info(f"[WebSocket] Started live stream for {phone} ch{channel}")
    
    async def _handle_stop_live(self, content):
        """
        Handle stop_live action.
        
        Args:
            content: {
                'action': 'stop_live',
                'phone': '123456789012',
                'channel': 1
            }
        """
        phone = content.get('phone')
        channel = content.get('channel', 1)
        
        if not phone:
            await self.send_json({
                'type': 'error',
                'message': 'Phone number required'
            })
            return
        
        # Unsubscribe from video updates
        device_manager.remove_websocket_client(phone, self)
        self.subscribed_devices.discard(phone)
        
        # Send stop command to device
        await self._send_stop_request(phone, channel)
        
        # Update streaming status
        device_manager.set_streaming(phone, False)
        
        await self.send_json({
            'type': 'response',
            'action': 'stop_live',
            'success': True,
            'phone': phone,
            'channel': channel
        })
        
        logger.info(f"[WebSocket] Stopped live stream for {phone} ch{channel}")
    
    async def _send_stream_request(self, phone: str, channel: int, 
                                    stream_type: int) -> bool:
        """
        Send stream request to device via JT808 server.
        
        Args:
            phone: Device phone/SIM number
            channel: Camera channel (1=Front, 2=Rear)
            stream_type: 0=Main (HD), 1=Sub (SD)
        
        Returns:
            True if request sent successfully
        """
        import os
        
        writer = device_manager.get_connection(phone)
        if not writer:
            logger.warning(f"[WebSocket] No JT808 connection for {phone}")
            return False
        
        try:
            # Build stream request message
            server_ip = os.environ.get('PUBLIC_IP', '82.180.145.220')
            video_port = int(os.environ.get('JT1078_PORT', 6664))
            seq_num = device_manager.get_next_seq(phone)
            
            message = build_realtime_av_request(
                phone=phone,
                channel=channel,
                server_ip=server_ip,
                tcp_port=video_port,
                stream_type=stream_type,
                seq_num=seq_num
            )
            
            writer.write(message)
            await writer.drain()
            
            logger.debug(f"[WebSocket] Sent stream request to {phone}")
            return True
            
        except Exception as e:
            logger.error(f"[WebSocket] Failed to send stream request to {phone}: {e}")
            return False
    
    async def _send_stop_request(self, phone: str, channel: int) -> bool:
        """
        Send stop stream request to device.
        
        Args:
            phone: Device phone/SIM number
            channel: Camera channel
        
        Returns:
            True if request sent successfully
        """
        writer = device_manager.get_connection(phone)
        if not writer:
            return False
        
        try:
            seq_num = device_manager.get_next_seq(phone)
            
            message = build_av_control(
                phone=phone,
                channel=channel,
                control_cmd=0,  # Close
                close_type=0,   # Close all
                seq_num=seq_num
            )
            
            writer.write(message)
            await writer.drain()
            
            logger.debug(f"[WebSocket] Sent stop request to {phone}")
            return True
            
        except Exception as e:
            logger.error(f"[WebSocket] Failed to send stop request to {phone}: {e}")
            return False
    
    async def send_video_data(self, data: dict):
        """
        Send video data to client (called by device_manager).
        
        Args:
            data: Video data dict with type, phone, channel, data (base64)
        """
        await self.send_json(data)
