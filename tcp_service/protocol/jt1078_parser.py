"""
JT1078 Video Protocol Parser

Implements parsing of JT1078 video stream packets for dashcam video transmission.
Based on JT/T 1078-2016 standard.
"""
import struct
import logging
from typing import Optional, Dict, Any

from .constants import JT1078DataType, JT1078SubpackageType, JT1078_HEADER
from .jt808_parser import parse_bcd

logger = logging.getLogger(__name__)


def parse_video_packet(data: bytes) -> Optional[Dict[str, Any]]:
    """
    Parse a JT1078 video packet.
    
    Packet structure:
        - Header (4 bytes): 0x30316364 ("01cd")
        - RTP byte 1 (1 byte): V(2) P(1) X(1) CC(4)
        - RTP byte 2 (1 byte): M(1) PT(7)
        - Sequence number (2 bytes)
        - SIM number (6 bytes, BCD)
        - Channel (1 byte)
        - Data type (1 byte): type(4) + subpackage(4)
        - Timestamp (8 bytes, video only)
        - I-frame interval (2 bytes, video only)
        - Frame interval (2 bytes, video only)
        - Body length (2 bytes)
        - Body (variable)
    
    Args:
        data: Raw packet bytes
    
    Returns:
        Parsed packet dict or None if invalid
    """
    if len(data) < 30:
        return None
    
    # Check header
    if data[0:4] != JT1078_HEADER:
        return None
    
    try:
        # Parse RTP-like header
        rtp_byte1 = data[4]
        rtp_byte2 = data[5]
        
        # RTP version (should be 2)
        version = (rtp_byte1 >> 6) & 0x03
        padding = (rtp_byte1 >> 5) & 0x01
        extension = (rtp_byte1 >> 4) & 0x01
        cc = rtp_byte1 & 0x0F  # CSRC count
        
        # Marker and payload type
        marker = (rtp_byte2 >> 7) & 0x01
        payload_type = rtp_byte2 & 0x7F  # 98=H.264, 99=H.265
        
        # Sequence number
        seq_num = struct.unpack(">H", data[6:8])[0]
        
        # SIM number (BCD, 6 bytes)
        sim_bcd = data[8:14]
        sim = parse_bcd(sim_bcd)
        
        # Channel number (1=Front, 2=Rear, etc.)
        channel = data[14]
        
        # Data type and subpackage info (byte 15)
        data_type_byte = data[15]
        data_type = (data_type_byte >> 4) & 0x0F  # 0=I, 1=P, 2=B, 3=Audio, 4=Transparent
        subpackage = data_type_byte & 0x0F  # 0=Atomic, 1=First, 2=Last, 3=Middle
        
        # Parse fields based on data type
        offset = 16
        timestamp = 0
        iframe_interval = 0
        frame_interval = 0
        
        if data_type <= 2:  # Video frame (I, P, B)
            if len(data) >= 28:
                timestamp = struct.unpack(">Q", data[16:24])[0]
                iframe_interval = struct.unpack(">H", data[24:26])[0]
                frame_interval = struct.unpack(">H", data[26:28])[0]
                offset = 28
        elif data_type == 3:  # Audio frame
            if len(data) >= 24:
                timestamp = struct.unpack(">Q", data[16:24])[0]
                offset = 24
        else:  # Transparent data
            offset = 16
        
        # Data body length and data
        if len(data) >= offset + 2:
            body_length = struct.unpack(">H", data[offset:offset+2])[0]
            body = data[offset+2:offset+2+body_length]
        else:
            body_length = 0
            body = b""
        
        return {
            "version": version,
            "padding": padding,
            "extension": extension,
            "cc": cc,
            "marker": marker,
            "payload_type": payload_type,
            "seq_num": seq_num,
            "sim": sim,
            "channel": channel,
            "data_type": data_type,
            "subpackage": subpackage,
            "timestamp": timestamp,
            "iframe_interval": iframe_interval,
            "frame_interval": frame_interval,
            "body_length": body_length,
            "body": body,
            "is_keyframe": data_type == JT1078DataType.I_FRAME,
            "is_audio": data_type == JT1078DataType.AUDIO,
            "is_video": data_type in (JT1078DataType.I_FRAME, JT1078DataType.P_FRAME, JT1078DataType.B_FRAME),
        }
    
    except Exception as e:
        logger.error(f"Failed to parse JT1078 packet: {e}")
        return None


def get_packet_size(data: bytes) -> int:
    """
    Calculate the total size of a JT1078 packet from its header.
    
    Returns:
        Total packet size in bytes, or 0 if invalid
    """
    if len(data) < 30:
        return 0
    
    if data[0:4] != JT1078_HEADER:
        return 0
    
    try:
        data_type_byte = data[15]
        data_type = (data_type_byte >> 4) & 0x0F
        
        # Determine header size based on data type
        if data_type <= 2:  # Video
            header_size = 30
        elif data_type == 3:  # Audio
            header_size = 26
        else:  # Transparent
            header_size = 18
        
        if len(data) < header_size:
            return 0
        
        # Get body length from appropriate offset
        if data_type <= 2:
            body_length = struct.unpack(">H", data[28:30])[0]
        elif data_type == 3:
            body_length = struct.unpack(">H", data[24:26])[0]
        else:
            body_length = struct.unpack(">H", data[16:18])[0]
        
        return header_size + body_length
    
    except Exception:
        return 0


def find_packet_start(data: bytes) -> int:
    """
    Find the start position of a JT1078 packet in a buffer.
    
    Returns:
        Index of packet start, or -1 if not found
    """
    return data.find(JT1078_HEADER)


class JT1078PacketAssembler:
    """
    Assembles fragmented JT1078 video packets into complete frames.
    
    JT1078 can split large frames across multiple packets using subpackage types:
        0 = Atomic (complete in one packet)
        1 = First fragment
        2 = Last fragment
        3 = Middle fragment
    """
    
    def __init__(self):
        self.buffers: Dict[str, Dict[int, bytearray]] = {}  # sim -> channel -> buffer
    
    def _get_buffer_key(self, sim: str, channel: int) -> str:
        return f"{sim}_{channel}"
    
    def process_packet(self, packet: Dict[str, Any]) -> Optional[bytes]:
        """
        Process a JT1078 packet and return complete frame data when available.
        
        Args:
            packet: Parsed packet dict from parse_video_packet()
        
        Returns:
            Complete frame bytes if ready, None otherwise
        """
        sim = packet["sim"]
        channel = packet["channel"]
        subpackage = packet["subpackage"]
        body = packet["body"]
        
        key = self._get_buffer_key(sim, channel)
        
        if subpackage == JT1078SubpackageType.ATOMIC:
            # Complete frame in one packet
            return body
        
        elif subpackage == JT1078SubpackageType.FIRST:
            # Start of fragmented frame
            if key not in self.buffers:
                self.buffers[key] = {}
            self.buffers[key][channel] = bytearray(body)
            return None
        
        elif subpackage == JT1078SubpackageType.MIDDLE:
            # Middle fragment
            if key in self.buffers and channel in self.buffers[key]:
                self.buffers[key][channel].extend(body)
            return None
        
        elif subpackage == JT1078SubpackageType.LAST:
            # Last fragment - return complete frame
            if key in self.buffers and channel in self.buffers[key]:
                self.buffers[key][channel].extend(body)
                complete_frame = bytes(self.buffers[key][channel])
                del self.buffers[key][channel]
                return complete_frame
            return None
        
        return None
    
    def clear_buffer(self, sim: str, channel: int = None):
        """Clear buffer for a device/channel."""
        key = self._get_buffer_key(sim, channel) if channel else None
        
        if key and key in self.buffers:
            if channel and channel in self.buffers[key]:
                del self.buffers[key][channel]
            elif not channel:
                del self.buffers[key]
        elif not channel:
            # Clear all buffers for this SIM
            keys_to_remove = [k for k in self.buffers.keys() if k.startswith(f"{sim}_")]
            for k in keys_to_remove:
                del self.buffers[k]
    
    def clear_all(self):
        """Clear all buffers."""
        self.buffers.clear()
