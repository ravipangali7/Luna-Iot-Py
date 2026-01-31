"""
JT808 TCP Server

Asyncio-based TCP server for handling JT808 protocol communication with dashcam devices.
Listens on port 6665 for GPS signaling and control messages.
Uses Redis channel layer for cross-process communication with WebSocket consumers.
"""
import asyncio
import logging
from typing import Optional

from django.conf import settings

from ..protocol.jt808_parser import parse_message, build_realtime_av_request, build_av_control
from ..protocol.constants import JT808_FLAG
from ..handlers.message_router import MessageRouter
from .device_manager import DeviceManager

logger = logging.getLogger(__name__)


class JT808Server:
    """
    TCP Server for JT808 Protocol.
    
    Handles:
    - Device registration and authentication
    - Heartbeat messages
    - Location reports
    - Command responses
    
    Messages are framed by 0x7E delimiters.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 6665, 
                 device_manager: DeviceManager = None):
        """
        Initialize JT808 server.
        
        Args:
            host: Host to bind to
            port: Port to listen on
            device_manager: DeviceManager instance
        """
        self.host = host
        self.port = port
        self.device_manager = device_manager or DeviceManager()
        self.router = MessageRouter(self.device_manager)
        self.server: Optional[asyncio.Server] = None
        self._running = False
    
    async def start(self):
        """Start the TCP server and channel layer listener."""
        self.server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port
        )
        self._running = True
        
        addr = self.server.sockets[0].getsockname()
        logger.info(f"JT808 Server started on {addr[0]}:{addr[1]}")
        
        # Start channel layer listener for stream commands
        asyncio.create_task(self._listen_channel_layer())
        
        async with self.server:
            await self.server.serve_forever()
    
    async def _listen_channel_layer(self):
        """Listen for stream commands from WebSocket consumers via Redis channel layer."""
        try:
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            
            if not channel_layer:
                logger.warning("[JT808] No channel layer configured, stream commands disabled")
                return
            
            # Create a unique channel name for this server instance
            channel_name = f'tcp_server_{id(self)}'
            
            # Join the tcp_commands group
            await channel_layer.group_add('tcp_commands', channel_name)
            logger.info(f"[JT808] Joined tcp_commands group as {channel_name}")
            
            while self._running:
                try:
                    # Receive message from channel layer
                    message = await asyncio.wait_for(
                        channel_layer.receive(channel_name),
                        timeout=5.0
                    )
                    
                    msg_type = message.get('type', '')
                    
                    if msg_type == 'stream.request':
                        await self._handle_stream_request(message)
                    elif msg_type == 'stream.stop':
                        await self._handle_stream_stop(message)
                    else:
                        logger.debug(f"[JT808] Unknown channel message type: {msg_type}")
                        
                except asyncio.TimeoutError:
                    # No message received, continue listening
                    continue
                except Exception as e:
                    logger.error(f"[JT808] Error processing channel message: {e}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"[JT808] Channel layer listener error: {e}")
    
    async def _handle_stream_request(self, message: dict):
        """Handle stream request from WebSocket consumer."""
        phone = message.get('phone')
        channel = message.get('channel', 1)
        stream_type = message.get('stream_type', 0)
        server_ip = message.get('server_ip', settings.TCP_SERVICE_PUBLIC_IP)
        video_port = message.get('video_port', settings.TCP_SERVICE_JT1078_PORT)
        
        logger.info(f"[JT808] Received stream request for {phone} ch{channel}")
        
        # Get device connection
        writer = self.device_manager.get_connection(phone)
        if not writer:
            logger.warning(f"[JT808] No connection for device {phone}")
            return
        
        try:
            # Build and send stream request
            seq_num = self.device_manager.get_next_seq(phone)
            request = build_realtime_av_request(
                phone=phone,
                channel=channel,
                server_ip=server_ip,
                tcp_port=video_port,
                stream_type=stream_type,
                seq_num=seq_num
            )
            
            writer.write(request)
            await writer.drain()
            
            # Update streaming status
            self.device_manager.set_streaming(phone, True, channel)
            
            logger.info(f"[JT808] Sent stream request to {phone} ch{channel}")
            
        except Exception as e:
            logger.error(f"[JT808] Failed to send stream request to {phone}: {e}")
    
    async def _handle_stream_stop(self, message: dict):
        """Handle stream stop request from WebSocket consumer."""
        phone = message.get('phone')
        channel = message.get('channel', 1)
        
        logger.info(f"[JT808] Received stream stop for {phone} ch{channel}")
        
        # Get device connection
        writer = self.device_manager.get_connection(phone)
        if not writer:
            logger.warning(f"[JT808] No connection for device {phone}")
            return
        
        try:
            # Build and send stop request
            seq_num = self.device_manager.get_next_seq(phone)
            request = build_av_control(
                phone=phone,
                channel=channel,
                control_cmd=0,  # Close
                close_type=0,   # Close all
                seq_num=seq_num
            )
            
            writer.write(request)
            await writer.drain()
            
            # Update streaming status
            self.device_manager.set_streaming(phone, False)
            
            logger.info(f"[JT808] Sent stop request to {phone} ch{channel}")
            
        except Exception as e:
            logger.error(f"[JT808] Failed to send stop request to {phone}: {e}")
    
    async def stop(self):
        """Stop the TCP server."""
        self._running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("JT808 Server stopped")
    
    async def _handle_client(self, reader: asyncio.StreamReader, 
                              writer: asyncio.StreamWriter):
        """
        Handle a client connection.
        
        Args:
            reader: StreamReader for receiving data
            writer: StreamWriter for sending responses
        """
        addr = writer.get_extra_info('peername')
        logger.info(f"[JT808] New connection from {addr}")
        
        buffer = b""
        phone = None
        
        try:
            while self._running:
                try:
                    data = await asyncio.wait_for(reader.read(4096), timeout=120.0)
                except asyncio.TimeoutError:
                    logger.warning(f"[JT808] Connection timeout from {addr}")
                    break
                
                if not data:
                    break
                
                buffer += data
                
                # Process complete messages (framed by 0x7E)
                while len(buffer) >= 2:
                    # Find start flag
                    start = buffer.find(bytes([JT808_FLAG]))
                    if start < 0:
                        buffer = b""
                        break
                    
                    if start > 0:
                        buffer = buffer[start:]
                    
                    # Find end flag (after start)
                    end = buffer.find(bytes([JT808_FLAG]), 1)
                    if end < 0:
                        break  # Wait for more data
                    
                    # Extract complete message
                    message_data = buffer[:end + 1]
                    buffer = buffer[end + 1:]
                    
                    # Parse and handle message
                    msg = parse_message(message_data)
                    if msg:
                        # Get message type name
                        msg_id = msg.get('msg_id', 0)
                        msg_names = {
                            0x0001: "TERMINAL_RESPONSE",
                            0x0002: "HEARTBEAT",
                            0x0100: "REGISTRATION",
                            0x0102: "AUTH",
                            0x0200: "LOCATION",
                        }
                        msg_name = msg_names.get(msg_id, "UNKNOWN")
                        
                        # Log parsed message details
                        body_hex = msg.get('body', b'').hex().upper()[:100] if msg.get('body') else 'None'
                        logger.info(f"[JT808] Received {msg_name}(0x{msg_id:04X}): phone={msg.get('phone')}, seq={msg.get('seq_num')}, body_len={len(msg.get('body', b''))}")
                        
                        phone = msg.get("phone", phone)
                        
                        # Store IP address for device
                        if phone and self.device_manager:
                            device = self.device_manager.get_device(phone)
                            if device:
                                device['ip_address'] = addr[0]
                                device['port'] = addr[1]
                        
                        # Route message to handler
                        response = await self.router.route(msg, writer)
                        
                        if response:
                            writer.write(response)
                            await writer.drain()
        
        except asyncio.CancelledError:
            logger.info(f"[JT808] Connection cancelled from {addr}")
        except ConnectionResetError:
            logger.info(f"[JT808] Connection reset from {addr}")
        except Exception as e:
            logger.error(f"[JT808] Error handling client {addr}: {e}")
        finally:
            # Clean up connection
            if phone:
                await self._handle_disconnect(phone)
            
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            
            logger.info(f"[JT808] Connection closed from {addr}")
    
    async def _handle_disconnect(self, phone: str):
        """Handle device disconnection."""
        try:
            from asgiref.sync import sync_to_async
            from ..models import DashcamConnection
            
            # Update database using sync_to_async
            await sync_to_async(
                DashcamConnection.objects.filter(imei=phone).update,
                thread_sensitive=True
            )(
                is_connected=False,
                disconnected_at=self._get_nepal_datetime()
            )
        except Exception as e:
            logger.error(f"[JT808] Disconnect update error for {phone}: {e}")
        
        # Remove from memory manager
        if self.device_manager:
            self.device_manager.remove_device(phone)
    
    def _get_nepal_datetime(self):
        """Get current datetime in Nepal timezone."""
        from datetime import datetime, timedelta
        return datetime.utcnow() + timedelta(hours=5, minutes=45)


async def run_jt808_server(host: str = "0.0.0.0", port: int = 6665, 
                           device_manager: DeviceManager = None):
    """
    Run the JT808 server.
    
    This is a convenience function for starting the server.
    """
    server = JT808Server(host, port, device_manager)
    await server.start()
