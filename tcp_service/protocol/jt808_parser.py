"""
JT808 Protocol Parser and Builder

Implements parsing and building of JT808 protocol messages for dashcam communication.
Based on JT/T 808-2019 standard.
"""
import struct
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from .constants import JT808MsgID, JT808_FLAG

logger = logging.getLogger(__name__)


def escape_data(data: bytes) -> bytes:
    """
    Escape special bytes in message body before transmission.
    
    Rules:
        0x7E -> 0x7D 0x02
        0x7D -> 0x7D 0x01
    """
    result = bytearray()
    for b in data:
        if b == 0x7E:  # Flag byte
            result.extend([0x7D, 0x02])
        elif b == 0x7D:  # Escape byte
            result.extend([0x7D, 0x01])
        else:
            result.append(b)
    return bytes(result)


def unescape_data(data: bytes) -> bytes:
    """
    Unescape special bytes in received message body.
    
    Rules:
        0x7D 0x02 -> 0x7E
        0x7D 0x01 -> 0x7D
    """
    result = bytearray()
    i = 0
    while i < len(data):
        if data[i] == 0x7D and i + 1 < len(data):
            if data[i + 1] == 0x02:
                result.append(0x7E)
                i += 2
            elif data[i + 1] == 0x01:
                result.append(0x7D)
                i += 2
            else:
                result.append(data[i])
                i += 1
        else:
            result.append(data[i])
            i += 1
    return bytes(result)


def calculate_checksum(data: bytes) -> int:
    """
    Calculate XOR checksum of all bytes.
    
    The checksum is calculated over all bytes between (not including) the flag bytes.
    """
    checksum = 0
    for b in data:
        checksum ^= b
    return checksum


def parse_bcd(data: bytes) -> str:
    """
    Parse BCD (Binary-Coded Decimal) encoded phone number.
    
    Each byte contains two decimal digits:
        - High nibble (bits 4-7): first digit
        - Low nibble (bits 0-3): second digit
    """
    result = ""
    for b in data:
        result += f"{(b >> 4) & 0x0F}{b & 0x0F}"
    return result.lstrip("0") or "0"


def encode_bcd(number: str, length: int = 6) -> bytes:
    """
    Encode phone number to BCD format.
    
    Args:
        number: Phone number string (digits only)
        length: Output length in bytes (pads with leading zeros)
    """
    # Pad with zeros to required length
    number = number.zfill(length * 2)
    result = bytearray()
    for i in range(0, len(number), 2):
        high = int(number[i]) if i < len(number) else 0
        low = int(number[i + 1]) if i + 1 < len(number) else 0
        result.append((high << 4) | low)
    return bytes(result)


def parse_datetime_bcd(data: bytes) -> datetime:
    """
    Parse BCD encoded datetime (YY-MM-DD-HH-MM-SS, 6 bytes).
    
    Format: Year(2000+YY), Month, Day, Hour, Minute, Second
    """
    try:
        bcd_str = parse_bcd(data)
        if len(bcd_str) >= 12:
            year = 2000 + int(bcd_str[0:2])
            month = int(bcd_str[2:4])
            day = int(bcd_str[4:6])
            hour = int(bcd_str[6:8])
            minute = int(bcd_str[8:10])
            second = int(bcd_str[10:12])
            return datetime(year, month, day, hour, minute, second)
    except (ValueError, IndexError) as e:
        logger.warning(f"Failed to parse datetime BCD: {e}")
    return datetime.now()


def encode_datetime_bcd(dt: datetime) -> bytes:
    """
    Encode datetime to BCD format (YY-MM-DD-HH-MM-SS, 6 bytes).
    """
    s = f"{dt.year % 100:02d}{dt.month:02d}{dt.day:02d}{dt.hour:02d}{dt.minute:02d}{dt.second:02d}"
    return encode_bcd(s, 6)


def parse_message(data: bytes) -> Optional[Dict[str, Any]]:
    """
    Parse a complete JT808 message.
    
    Message structure:
        - Flag (0x7E) - 1 byte
        - Header - 12+ bytes
        - Body - variable length
        - Checksum - 1 byte
        - Flag (0x7E) - 1 byte
    
    Header structure (12 bytes minimum):
        - Message ID: 2 bytes (big-endian)
        - Body Properties: 2 bytes
        - Phone/SIM (BCD): 6 bytes
        - Sequence Number: 2 bytes
    
    Returns dict with parsed fields or None if invalid.
    """
    if len(data) < 12:
        return None
    
    # Remove start/end flags if present
    if data[0] == JT808_FLAG:
        data = data[1:]
    if len(data) > 0 and data[-1] == JT808_FLAG:
        data = data[:-1]
    
    # Unescape the data
    data = unescape_data(data)
    
    if len(data) < 12:
        return None
    
    # Verify checksum
    checksum = data[-1]
    calculated = calculate_checksum(data[:-1])
    if checksum != calculated:
        logger.warning(f"Checksum mismatch: received {checksum}, calculated {calculated}")
        # Continue anyway for flexibility
    
    # Parse header
    msg_id = struct.unpack(">H", data[0:2])[0]
    body_props = struct.unpack(">H", data[2:4])[0]
    phone_bcd = data[4:10]
    seq_num = struct.unpack(">H", data[10:12])[0]
    
    # Body properties bit fields
    body_length = body_props & 0x03FF  # Bits 0-9
    is_encrypted = (body_props >> 10) & 0x01  # Bit 10
    is_subpackage = (body_props >> 13) & 0x01  # Bit 13
    
    # Parse phone number
    phone = parse_bcd(phone_bcd)
    
    # Extract body
    body_start = 12
    if is_subpackage:
        body_start += 4  # Skip subpackage info (total_packets: 2, packet_seq: 2)
    
    body = data[body_start:-1] if body_start < len(data) - 1 else b""
    print(f"Body: {body}")
    print(f"Body length: {body_length}")
    print(f"Is encrypted: {is_encrypted}")
    print(f"Is subpackage: {is_subpackage}")
    print(f"Raw data: {data}")
    return {
        "msg_id": msg_id,
        "phone": phone,
        "seq_num": seq_num,
        "body": body,
        "body_length": body_length,
        "is_encrypted": is_encrypted,
        "is_subpackage": is_subpackage,
        "raw_data": data
    }


def build_message(msg_id: int, phone: str, seq_num: int, body: bytes = b"") -> bytes:
    """
    Build a JT808 message ready for transmission.
    
    Args:
        msg_id: Message ID (e.g., 0x8001 for platform general response)
        phone: Phone/SIM number string
        seq_num: Sequence number (0-65535)
        body: Message body bytes
    
    Returns:
        Complete message with flags, escaped content, and checksum
    """
    # Build header
    body_props = len(body) & 0x03FF  # Body length in bits 0-9
    phone_bcd = encode_bcd(phone, 6)
    
    header = struct.pack(">H", msg_id)
    header += struct.pack(">H", body_props)
    header += phone_bcd
    header += struct.pack(">H", seq_num)
    
    # Combine header and body
    message = header + body
    
    # Calculate checksum
    checksum = calculate_checksum(message)
    message += bytes([checksum])
    
    # Escape special bytes
    message = escape_data(message)
    
    # Add frame flags
    return bytes([JT808_FLAG]) + message + bytes([JT808_FLAG])


def build_general_response(phone: str, resp_seq: int, resp_msg_id: int, result: int, seq_num: int) -> bytes:
    """
    Build a Platform General Response message (0x8001).
    
    Args:
        phone: Terminal phone/SIM number
        resp_seq: Sequence number of the message being responded to
        resp_msg_id: Message ID of the message being responded to
        result: Response result (0=success, 1=fail, 2=error, 3=not supported)
        seq_num: Sequence number for this response message
    
    Returns:
        Complete response message
    """
    body = struct.pack(">H", resp_seq)  # Response sequence
    body += struct.pack(">H", resp_msg_id)  # Response message ID
    body += bytes([result])  # Result code
    
    return build_message(JT808MsgID.PLATFORM_GENERAL_RESPONSE, phone, seq_num, body)


def build_registration_response(phone: str, resp_seq: int, result: int, auth_code: str, seq_num: int) -> bytes:
    """
    Build a Registration Response message (0x8100).
    
    Args:
        phone: Terminal phone/SIM number
        resp_seq: Sequence number of the registration request
        result: Registration result (0=success, 1=vehicle registered, etc.)
        auth_code: Authentication code to assign (if successful)
        seq_num: Sequence number for this response
    
    Returns:
        Complete registration response message
    """
    body = struct.pack(">H", resp_seq)  # Response sequence
    body += bytes([result])  # Result code
    if result == 0:  # Success
        body += auth_code.encode('utf-8')  # Auth code
    
    return build_message(JT808MsgID.REGISTRATION_RESPONSE, phone, seq_num, body)


def build_realtime_av_request(phone: str, channel: int, server_ip: str, tcp_port: int, 
                               stream_type: int = 0, seq_num: int = 0) -> bytes:
    """
    Build a Real-time Audio/Video Request message (0x9101).
    
    Args:
        phone: Terminal phone/SIM number
        channel: Logical channel number (1=Front, 2=Rear)
        server_ip: Server IP address for video stream
        tcp_port: TCP port for video stream
        stream_type: 0=Main stream (HD), 1=Sub stream (SD)
        seq_num: Sequence number
    
    Returns:
        Complete AV request message
    """
    ip_bytes = server_ip.encode('utf-8')
    
    body = bytes([len(ip_bytes)])  # IP length
    body += ip_bytes  # Server IP
    body += struct.pack(">H", tcp_port)  # TCP port
    body += struct.pack(">H", 0)  # UDP port (not used)
    body += bytes([channel])  # Logical channel
    body += bytes([0])  # Data type: 0=AV
    body += bytes([stream_type])  # Stream type
    
    return build_message(JT808MsgID.REALTIME_AV_REQUEST, phone, seq_num, body)


def build_av_control(phone: str, channel: int, control_cmd: int, close_type: int = 0,
                     switch_stream: int = 0, seq_num: int = 0) -> bytes:
    """
    Build an Audio/Video Control message (0x9102).
    
    Args:
        phone: Terminal phone/SIM number
        channel: Logical channel number
        control_cmd: 0=Close, 1=Switch stream, 2=Pause, 3=Resume, 4=Close talk
        close_type: 0=Close all, 1=Close audio, 2=Close video
        switch_stream: 0=Main, 1=Sub
        seq_num: Sequence number
    
    Returns:
        Complete AV control message
    """
    body = bytes([channel])  # Logical channel
    body += bytes([control_cmd])  # Control command
    body += bytes([close_type])  # Close type
    body += bytes([switch_stream])  # Switch stream type
    
    return build_message(JT808MsgID.AV_CONTROL, phone, seq_num, body)


def parse_location_report(body: bytes) -> Optional[Dict[str, Any]]:
    """
    Parse a Location Report message body (0x0200).
    
    Body structure (28 bytes minimum):
        - Alarm flags: 4 bytes
        - Status flags: 4 bytes
        - Latitude: 4 bytes (×10^-6 degrees)
        - Longitude: 4 bytes (×10^-6 degrees)
        - Altitude: 2 bytes (meters)
        - Speed: 2 bytes (×0.1 km/h)
        - Direction: 2 bytes (degrees, 0-359)
        - Timestamp: 6 bytes (BCD: YY-MM-DD-HH-MM-SS)
        - Additional info: variable
    """
    if len(body) < 28:
        return None
    
    try:
        alarm_flags = struct.unpack(">I", body[0:4])[0]
        status_flags = struct.unpack(">I", body[4:8])[0]
        latitude = struct.unpack(">I", body[8:12])[0] / 1000000.0
        longitude = struct.unpack(">I", body[12:16])[0] / 1000000.0
        altitude = struct.unpack(">H", body[16:18])[0]
        speed = struct.unpack(">H", body[18:20])[0] / 10.0
        direction = struct.unpack(">H", body[20:22])[0]
        timestamp = parse_datetime_bcd(body[22:28])
        
        # Check latitude sign from status flags (bit 2)
        if status_flags & 0x04:
            latitude = -latitude
        # Check longitude sign from status flags (bit 3)
        if status_flags & 0x08:
            longitude = -longitude
        
        return {
            "alarm_flags": alarm_flags,
            "status_flags": status_flags,
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude,
            "speed": speed,
            "direction": direction,
            "timestamp": timestamp,
            "acc_on": bool(status_flags & 0x01),  # Bit 0: ACC status
            "positioned": bool(status_flags & 0x02),  # Bit 1: Positioning status
        }
    except Exception as e:
        logger.error(f"Failed to parse location report: {e}")
        return None


def parse_registration(body: bytes) -> Optional[Dict[str, Any]]:
    """
    Parse a Terminal Registration message body (0x0100).
    
    Body structure:
        - Province ID: 2 bytes
        - City ID: 2 bytes
        - Manufacturer: 5 bytes
        - Terminal Model: 20 bytes
        - Terminal ID: 7 bytes
        - License Plate Color: 1 byte
        - License Plate: variable
    """
    if len(body) < 37:
        return None
    
    try:
        province_id = struct.unpack(">H", body[0:2])[0]
        city_id = struct.unpack(">H", body[2:4])[0]
        manufacturer = body[4:9].decode('utf-8', errors='ignore').strip('\x00')
        terminal_model = body[9:29].decode('utf-8', errors='ignore').strip('\x00')
        terminal_id = body[29:36].decode('utf-8', errors='ignore').strip('\x00')
        plate_color = body[36]
        plate = body[37:].decode('utf-8', errors='ignore').strip('\x00') if len(body) > 37 else ""
        
        return {
            "province_id": province_id,
            "city_id": city_id,
            "manufacturer": manufacturer,
            "terminal_model": terminal_model,
            "terminal_id": terminal_id,
            "plate_color": plate_color,
            "plate": plate,
        }
    except Exception as e:
        logger.error(f"Failed to parse registration: {e}")
        return None
