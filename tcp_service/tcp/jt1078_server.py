"""
JT1078 Video TCP Server

Asyncio-based TCP server for handling JT1078 video streaming from dashcam devices.
Listens on port 6664 for video data and broadcasts to WebSocket clients.
"""
import asyncio
import logging
from typing import Optional, Dict

from ..protocol.jt1078_parser import parse_video_packet, find_packet_start, get_packet_size, JT1078PacketAssembler
from ..protocol.constants import JT1078_HEADER
from ..video.converter import VideoConverter
from .device_manager import DeviceManager

logger = logging.getLogger(__name__)


class JT1078Server:
    """
    TCP Server for JT1078 Video Protocol.
    
    Handles:
    - Video packet reception and parsing
    - Subpackage assembly for fragmented frames
    - H.264 to fMP4 conversion
    - Broadcasting to WebSocket clients
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 6664,
                 device_manager: DeviceManager = None):
        """
        Initialize JT1078 video server.
        
        Args:
            host: Host to bind to
            port: Port to listen on
            device_manager: DeviceManager instance for broadcasting
        """
        self.host = host
        self.port = port
        self.device_manager = device_manager or DeviceManager()
        self.server: Optional[asyncio.Server] = None
        self._running = False
        
        # Video converters per device/channel
        self.converters: Dict[str, VideoConverter] = {}
        self.assembler = JT1078PacketAssembler()
    
    async def start(self):
        """Start the TCP server."""
        self.server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port
        )
        self._running = True
        
        addr = self.server.sockets[0].getsockname()
        logger.info(f"JT1078 Video Server started on {addr[0]}:{addr[1]}")
        
        async with self.server:
            await self.server.serve_forever()
    
    async def stop(self):
        """Stop the TCP server."""
        self._running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("JT1078 Video Server stopped")
    
    def _get_converter_key(self, sim: str, channel: int) -> str:
        """Generate key for converter lookup."""
        return f"{sim}_{channel}"
    
    def _get_converter(self, sim: str, channel: int) -> VideoConverter:
        """Get or create video converter for device/channel."""
        key = self._get_converter_key(sim, channel)
        if key not in self.converters:
            self.converters[key] = VideoConverter()
        return self.converters[key]
    
    async def _handle_client(self, reader: asyncio.StreamReader,
                              writer: asyncio.StreamWriter):
        """
        Handle a video client connection.
        
        Args:
            reader: StreamReader for receiving data
            writer: StreamWriter (not typically used for video)
        """
        addr = writer.get_extra_info('peername')
        logger.info(f"[JT1078] New video connection from {addr}")
        
        buffer = b""
        current_sim = None
        
        try:
            while self._running:
                try:
                    data = await asyncio.wait_for(reader.read(65536), timeout=60.0)
                except asyncio.TimeoutError:
                    # Video connections may be idle, just continue
                    continue
                
                if not data:
                    break
                
                buffer += data
                
                # Process video packets
                while len(buffer) >= 30:
                    # Find JT1078 header
                    header_pos = find_packet_start(buffer)
                    
                    if header_pos < 0:
                        # No header found, keep last 3 bytes for partial header
                        buffer = buffer[-3:] if len(buffer) > 3 else buffer
                        break
                    
                    if header_pos > 0:
                        # Skip garbage before header
                        buffer = buffer[header_pos:]
                    
                    if len(buffer) < 30:
                        break
                    
                    # Get packet size
                    packet_size = get_packet_size(buffer)
                    if packet_size == 0:
                        # Invalid packet, skip 4 bytes
                        buffer = buffer[4:]
                        continue
                    
                    if len(buffer) < packet_size:
                        # Wait for more data
                        break
                    
                    # Extract and parse packet
                    packet_data = buffer[:packet_size]
                    buffer = buffer[packet_size:]
                    
                    packet = parse_video_packet(packet_data)
                    if not packet:
                        continue
                    
                    current_sim = packet["sim"]
                    
                    # Process video packet
                    await self._process_video_packet(packet)
        
        except asyncio.CancelledError:
            logger.info(f"[JT1078] Video connection cancelled from {addr}")
        except ConnectionResetError:
            logger.info(f"[JT1078] Video connection reset from {addr}")
        except Exception as e:
            logger.error(f"[JT1078] Error handling video client {addr}: {e}")
        finally:
            # Clean up
            if current_sim:
                self._cleanup_device(current_sim)
            
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            
            logger.info(f"[JT1078] Video connection closed from {addr}")
    
    async def _process_video_packet(self, packet: Dict) -> None:
        """
        Process a parsed video packet.
        
        Args:
            packet: Parsed JT1078 packet dict
        """
        sim = packet["sim"]
        channel = packet["channel"]
        
        # Skip audio for now
        if packet["is_audio"]:
            return
        
        # Get converter for this device/channel
        converter = self._get_converter(sim, channel)
        
        # Assemble fragmented frames
        frame_data = self.assembler.process_packet(packet)
        
        if frame_data:
            # Convert to fMP4 segment
            segment = converter.process_packet(frame_data, 0)  # 0 = atomic (already assembled)
            
            if segment:
                # Check if we need to send init segment first
                if converter.frame_count == 1:
                    init_seg = converter.get_init_segment()
                    if init_seg:
                        codec = converter.get_codec_string()
                        await self._broadcast_video(sim, init_seg, is_init=True, 
                                                   codec=codec, channel=channel)
                        logger.debug(f"[JT1078] Sent init segment for {sim} ch{channel}")
                
                # Broadcast video segment
                await self._broadcast_video(sim, segment, channel=channel)
    
    async def _broadcast_video(self, sim: str, data: bytes, is_init: bool = False,
                                codec: str = None, channel: int = 1) -> None:
        """
        Broadcast video data to WebSocket clients via Redis channel layer.
        
        Args:
            sim: Device SIM/phone number
            data: fMP4 segment data
            is_init: True if this is an init segment
            codec: Codec string (for init segment)
            channel: Camera channel
        """
        try:
            import base64
            from channels.layers import get_channel_layer
            
            channel_layer = get_channel_layer()
            if channel_layer:
                # Encode data as base64
                data_b64 = base64.b64encode(data).decode('utf-8')
                
                # Send to video group for this device
                await channel_layer.group_send(f'video_{sim}', {
                    'type': 'video.data',
                    'video_type': 'init_segment' if is_init else 'video',
                    'phone': sim,
                    'channel': channel,
                    'data': data_b64,
                    'codec': codec if is_init else None,
                })
            else:
                # Fallback to legacy device_manager broadcast
                if self.device_manager:
                    await self.device_manager.broadcast_video(
                        phone=sim,
                        data=data,
                        is_init=is_init,
                        codec=codec,
                        channel=channel
                    )
        except Exception as e:
            logger.error(f"[JT1078] Error broadcasting video for {sim}: {e}")
    
    def _cleanup_device(self, sim: str) -> None:
        """Clean up resources for a disconnected device."""
        # Remove converters for this device
        keys_to_remove = [k for k in self.converters.keys() if k.startswith(f"{sim}_")]
        for key in keys_to_remove:
            del self.converters[key]
        
        # Clear assembler buffers
        self.assembler.clear_buffer(sim)
        
        # Update streaming status
        if self.device_manager:
            self.device_manager.set_streaming(sim, False)


async def run_jt1078_server(host: str = "0.0.0.0", port: int = 6664,
                            device_manager: DeviceManager = None):
    """
    Run the JT1078 video server.
    
    This is a convenience function for starting the server.
    """
    server = JT1078Server(host, port, device_manager)
    await server.start()
