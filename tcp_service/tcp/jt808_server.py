"""
JT808 TCP Server

Asyncio-based TCP server for handling JT808 protocol communication with dashcam devices.
Listens on port 6665 for GPS signaling and control messages.
"""
import asyncio
import logging
from typing import Optional

from ..protocol.jt808_parser import parse_message
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
        """Start the TCP server."""
        self.server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port
        )
        self._running = True
        
        addr = self.server.sockets[0].getsockname()
        logger.info(f"JT808 Server started on {addr[0]}:{addr[1]}")
        
        async with self.server:
            await self.server.serve_forever()
    
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
                
                # Print raw received data
                print(f"[JT808] RAW DATA from {addr}: {data.hex().upper()}")
                
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
                    
                    # Print complete message frame
                    print(f"[JT808] MESSAGE FRAME: {message_data.hex().upper()}")
                    
                    # Parse and handle message
                    msg = parse_message(message_data)
                    if msg:
                        print(f"[JT808] PARSED: msg_id=0x{msg.get('msg_id', 0):04X}, phone={msg.get('phone')}, seq={msg.get('seq_num')}")
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
                self._handle_disconnect(phone)
            
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            
            logger.info(f"[JT808] Connection closed from {addr}")
    
    def _handle_disconnect(self, phone: str):
        """Handle device disconnection."""
        try:
            from asgiref.sync import async_to_sync
            from ..models import DashcamConnection
            
            # Update database
            DashcamConnection.objects.filter(imei=phone).update(
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
