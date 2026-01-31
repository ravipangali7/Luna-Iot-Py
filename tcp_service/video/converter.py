"""
H.264 to fMP4 Video Converter

Converts raw H.264 NAL units from JT1078 packets to fragmented MP4 format
for browser playback using MediaSource Extensions (MSE).
"""
import logging
from typing import Optional, List, Tuple

from .fmp4_builder import FMP4Builder
from ..protocol.constants import DEFAULT_VIDEO_WIDTH, DEFAULT_VIDEO_HEIGHT, DEFAULT_VIDEO_FPS, DEFAULT_VIDEO_TIMESCALE

logger = logging.getLogger(__name__)


class VideoConverter:
    """
    Converts H.264 NAL units to fMP4 segments.
    
    Browser MSE requires:
    1. Init segment (ftyp + moov) - sent once with codec info
    2. Media segments (moof + mdat) - sent for each frame
    
    NAL unit types:
    - Type 1: Non-IDR slice (P/B frame)
    - Type 5: IDR slice (I-frame / keyframe)
    - Type 7: SPS (Sequence Parameter Set)
    - Type 8: PPS (Picture Parameter Set)
    """
    
    def __init__(self):
        self.initialized = False
        self.init_segment: Optional[bytes] = None
        self.width = DEFAULT_VIDEO_WIDTH
        self.height = DEFAULT_VIDEO_HEIGHT
        self.fps = DEFAULT_VIDEO_FPS
        self.timescale = DEFAULT_VIDEO_TIMESCALE
        self.sps: Optional[bytes] = None
        self.pps: Optional[bytes] = None
        self.frame_count = 0
        self.builder = FMP4Builder()
        
        # Buffer for assembling fragmented frames
        self.frame_accumulator = b""
    
    def process_packet(self, body: bytes, subpackage: int) -> Optional[bytes]:
        """
        Process a JT1078 packet and return fMP4 segment when ready.
        
        Args:
            body: NAL unit data from JT1078 packet
            subpackage: Subpackage type (0=Atomic, 1=First, 2=Last, 3=Middle)
        
        Returns:
            fMP4 media segment bytes, or None if not ready
        """
        if subpackage == 0:  # Atomic - complete frame
            return self.add_nal_unit(body)
        elif subpackage == 1:  # First fragment
            self.frame_accumulator = body
            return None
        elif subpackage == 3:  # Middle fragment
            self.frame_accumulator += body
            return None
        elif subpackage == 2:  # Last fragment
            self.frame_accumulator += body
            complete_frame = self.frame_accumulator
            self.frame_accumulator = b""
            return self.add_nal_unit(complete_frame)
        return None
    
    def add_nal_unit(self, nal_data: bytes) -> Optional[bytes]:
        """
        Process NAL units and return fMP4 segment when ready.
        
        Args:
            nal_data: H.264 data (may contain multiple NAL units)
        
        Returns:
            fMP4 media segment bytes, or None
        """
        if not nal_data or len(nal_data) < 4:
            return None
        
        # Split data into individual NAL units
        nal_units = self._split_nal_units(nal_data)
        segment = None
        
        for nal_unit in nal_units:
            if not nal_unit:
                continue
            
            # NAL type is in bits 0-4 of first byte
            nal_type = nal_unit[0] & 0x1F
            
            if nal_type == 7:  # SPS
                self.sps = nal_unit
                self._parse_sps(nal_unit)
                logger.debug(f"Got SPS: {len(nal_unit)} bytes, {self.width}x{self.height}")
            
            elif nal_type == 8:  # PPS
                self.pps = nal_unit
                logger.debug(f"Got PPS: {len(nal_unit)} bytes")
            
            elif nal_type == 5:  # IDR frame (keyframe)
                if self.sps and self.pps and not self.initialized:
                    self.initialized = True
                    self.init_segment = self._create_init_segment()
                    logger.info(f"Initialized video: {self.width}x{self.height}, codec={self._get_codec_string()}")
                
                if self.initialized:
                    segment = self._create_media_segment(nal_unit, is_keyframe=True)
                    self.frame_count += 1
            
            elif nal_type == 1:  # Non-IDR frame
                if self.initialized:
                    segment = self._create_media_segment(nal_unit, is_keyframe=False)
                    self.frame_count += 1
        
        return segment
    
    def _split_nal_units(self, data: bytes) -> List[bytes]:
        """
        Split data containing multiple NAL units with Annex B start codes.
        
        H.264 Annex B uses:
        - 4-byte start code: 00 00 00 01
        - 3-byte start code: 00 00 01
        """
        nal_units = []
        i = 0
        
        while i < len(data) - 3:
            start_code_len = 0
            
            # Check for 4-byte start code (00 00 00 01)
            if data[i:i+4] == b'\x00\x00\x00\x01':
                start_code_len = 4
            # Check for 3-byte start code (00 00 01)
            elif data[i:i+3] == b'\x00\x00\x01':
                start_code_len = 3
            
            if start_code_len > 0:
                nal_start = i + start_code_len
                # Find next start code
                nal_end = self._find_next_start_code(data, nal_start)
                
                if nal_end > nal_start:
                    nal_unit = data[nal_start:nal_end]
                    if len(nal_unit) > 0:
                        nal_units.append(nal_unit)
                
                i = nal_end
            else:
                i += 1
        
        # If no start codes found, treat entire data as single NAL unit
        if not nal_units and len(data) > 0:
            nal_units.append(data)
        
        return nal_units
    
    def _find_next_start_code(self, data: bytes, start: int) -> int:
        """Find the position of the next start code."""
        i = start
        while i < len(data) - 2:
            if data[i:i+3] == b'\x00\x00\x01':
                # Check if it's a 4-byte start code
                if i > 0 and data[i-1] == 0:
                    return i - 1
                return i
            i += 1
        return len(data)
    
    def _parse_sps(self, sps: bytes) -> None:
        """
        Parse SPS to extract video dimensions.
        
        This is a simplified parser - full SPS parsing is complex.
        We extract profile, level, and try to get dimensions.
        """
        if len(sps) < 4:
            return
        
        # Profile and level are at fixed positions
        profile_idc = sps[1]
        level_idc = sps[3]
        
        # Default dimensions based on level
        level_dimensions = {
            30: (1280, 720),   # Level 3.0
            31: (1280, 720),   # Level 3.1
            32: (1920, 1080),  # Level 3.2
            40: (1920, 1080),  # Level 4.0
            41: (1920, 1080),  # Level 4.1
            42: (2048, 1080),  # Level 4.2
            50: (2560, 1920),  # Level 5.0
            51: (4096, 2160),  # Level 5.1
        }
        
        if level_idc in level_dimensions:
            self.width, self.height = level_dimensions[level_idc]
        
        # Try to parse actual dimensions from SPS (complex due to exp-golomb coding)
        # For simplicity, we use reasonable defaults
        logger.debug(f"SPS: profile={profile_idc}, level={level_idc}, dim={self.width}x{self.height}")
    
    def _create_init_segment(self) -> bytes:
        """Create the initialization segment (ftyp + moov)."""
        return self.builder.build_init_segment(
            self.width, 
            self.height, 
            self.sps, 
            self.pps
        )
    
    def _create_media_segment(self, nal_data: bytes, is_keyframe: bool) -> bytes:
        """Create a media segment (moof + mdat)."""
        # Calculate timing
        sample_duration = self.timescale // self.fps  # e.g., 3600 for 25fps at 90kHz
        decode_time = self.frame_count * sample_duration
        
        return self.builder.build_media_segment(
            nal_data=nal_data,
            sequence_number=self.frame_count + 1,
            decode_time=decode_time,
            duration=sample_duration,
            is_keyframe=is_keyframe,
            sps=self.sps,
            pps=self.pps
        )
    
    def _get_codec_string(self) -> str:
        """
        Generate codec string from SPS for MediaSource.
        
        Format: avc1.XXYYZZ where XX=profile, YY=constraints, ZZ=level
        """
        if self.sps and len(self.sps) >= 4:
            profile = self.sps[1]
            constraints = self.sps[2]
            level = self.sps[3]
            return f"avc1.{profile:02X}{constraints:02X}{level:02X}"
        return "avc1.640028"  # Default: High Profile, Level 4.0
    
    def get_init_segment(self) -> Optional[bytes]:
        """Get the initialization segment if available."""
        return self.init_segment
    
    def get_codec_string(self) -> str:
        """Get the codec string for MediaSource."""
        return self._get_codec_string()
    
    def get_dimensions(self) -> Tuple[int, int]:
        """Get video dimensions (width, height)."""
        return (self.width, self.height)
    
    def is_initialized(self) -> bool:
        """Check if converter has received SPS/PPS and is ready."""
        return self.initialized
    
    def reset(self):
        """Reset converter state for a new stream."""
        self.initialized = False
        self.init_segment = None
        self.sps = None
        self.pps = None
        self.frame_count = 0
        self.frame_accumulator = b""
