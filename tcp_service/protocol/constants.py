"""
JT808/JT1078 Protocol Constants

Based on the JT/T 808-2019 and JT/T 1078-2016 standards.
"""
from enum import IntEnum


class JT808MsgID(IntEnum):
    """JT808 Message IDs"""
    # Terminal -> Platform
    TERMINAL_GENERAL_RESPONSE = 0x0001
    TERMINAL_HEARTBEAT = 0x0002
    TERMINAL_LOGOUT = 0x0003
    TERMINAL_REGISTRATION = 0x0100
    TERMINAL_AUTH = 0x0102
    LOCATION_REPORT = 0x0200
    LOCATION_QUERY_RESPONSE = 0x0201
    AV_ATTRIBUTES = 0x1003
    FILE_LIST_RESPONSE = 0x1205
    
    # Platform -> Terminal
    PLATFORM_GENERAL_RESPONSE = 0x8001
    REGISTRATION_RESPONSE = 0x8100
    QUERY_TERMINAL_PARAMS = 0x8104
    QUERY_LOCATION = 0x8201
    QUERY_AV_ATTRIBUTES = 0x9003
    REALTIME_AV_REQUEST = 0x9101
    AV_CONTROL = 0x9102
    QUERY_FILE_LIST = 0x9205
    PLAYBACK_REQUEST = 0x9201
    PLAYBACK_CONTROL = 0x9202


class JT808ResponseResult(IntEnum):
    """JT808 Response Result Codes"""
    SUCCESS = 0
    FAIL = 1
    MSG_ERROR = 2
    NOT_SUPPORTED = 3
    ALARM_CONFIRMED = 4


class JT808RegistrationResult(IntEnum):
    """JT808 Registration Response Result Codes"""
    SUCCESS = 0
    VEHICLE_REGISTERED = 1
    NO_VEHICLE = 2
    TERMINAL_REGISTERED = 3
    NO_TERMINAL = 4


class JT1078DataType(IntEnum):
    """JT1078 Video Data Types (high nibble of data_type byte)"""
    I_FRAME = 0  # Keyframe
    P_FRAME = 1  # Predictive frame
    B_FRAME = 2  # Bidirectional frame
    AUDIO = 3    # Audio frame
    TRANSPARENT = 4  # Transparent data


class JT1078SubpackageType(IntEnum):
    """JT1078 Subpackage Types (low nibble of data_type byte)"""
    ATOMIC = 0   # Complete in one packet
    FIRST = 1    # First fragment
    LAST = 2     # Last fragment
    MIDDLE = 3   # Middle fragment


class JT1078PayloadType(IntEnum):
    """JT1078 RTP Payload Types"""
    H264 = 98
    H265 = 99
    G711A = 6
    G711U = 7
    G726 = 8
    AAC = 19


class JT1078Channel(IntEnum):
    """JT1078 Camera Channels"""
    FRONT = 1
    REAR = 2
    LEFT = 3
    RIGHT = 4
    INSIDE = 5


class JT1078StreamType(IntEnum):
    """JT1078 Stream Types"""
    MAIN = 0  # Main stream (HD)
    SUB = 1   # Sub stream (SD)


class JT1078AVType(IntEnum):
    """JT1078 Audio/Video Types"""
    AV = 0     # Audio + Video
    AUDIO = 1  # Audio only
    VIDEO = 2  # Video only


# JT808 Protocol Frame Markers
JT808_FLAG = 0x7E

# JT1078 Video Packet Header
JT1078_HEADER = bytes([0x30, 0x31, 0x63, 0x64])  # "01cd" in ASCII

# Default Video Parameters
DEFAULT_VIDEO_WIDTH = 1280
DEFAULT_VIDEO_HEIGHT = 720
DEFAULT_VIDEO_FPS = 25
DEFAULT_VIDEO_TIMESCALE = 90000  # 90kHz for MPEG timing

# SMS Command Templates for BSJ Dashcam
SMS_COMMAND_SERVER_POINT = "<SPBSJ*P:BSJGPS*D:{ip},{port}>"
SMS_COMMAND_RESET = "<SPBSJ*P:BSJGPS*Q:0,0>"
