"""
fMP4 (Fragmented MP4) Builder

Builds fragmented MP4 boxes for browser playback using MediaSource Extensions.
Based on ISO/IEC 14496-12 (MP4 file format) specification.
"""
import struct
from typing import Optional


class FMP4Builder:
    """
    Builder for fragmented MP4 (fMP4) segments.
    
    fMP4 consists of:
    - Init segment: ftyp + moov (sent once at start)
    - Media segments: moof + mdat (sent for each frame/group)
    """
    
    def __init__(self):
        self.timescale = 90000  # 90kHz, standard for MPEG
    
    def box(self, box_type: bytes, data: bytes) -> bytes:
        """
        Create an MP4 box (atom).
        
        Structure:
            - Size (4 bytes, big-endian)
            - Type (4 bytes, ASCII)
            - Data (variable)
        """
        size = 8 + len(data)
        return struct.pack('>I', size) + box_type + data
    
    def build_ftyp(self) -> bytes:
        """
        Build File Type Box (ftyp).
        
        Declares the file type and compatible brands.
        """
        major_brand = b'isom'
        minor_version = struct.pack('>I', 512)
        compatible_brands = b'isomiso2avc1mp41'
        
        return self.box(b'ftyp', major_brand + minor_version + compatible_brands)
    
    def build_moov(self, width: int, height: int, sps: bytes, pps: bytes) -> bytes:
        """
        Build Movie Box (moov) for init segment.
        
        Contains:
            - mvhd: Movie header
            - trak: Track (video)
            - mvex: Movie extends (for fragmented MP4)
        """
        mvhd = self._build_mvhd()
        trak = self._build_trak(width, height, sps, pps)
        mvex = self._build_mvex()
        
        return self.box(b'moov', mvhd + trak + mvex)
    
    def _build_mvhd(self) -> bytes:
        """Build Movie Header Box (mvhd)."""
        data = bytes([
            0x00,  # version
            0x00, 0x00, 0x00,  # flags
        ])
        data += struct.pack('>I', 0)  # creation_time
        data += struct.pack('>I', 0)  # modification_time
        data += struct.pack('>I', self.timescale)  # timescale
        data += struct.pack('>I', 0)  # duration
        data += struct.pack('>I', 0x00010000)  # rate (1.0)
        data += struct.pack('>H', 0x0100)  # volume (1.0)
        data += b'\x00' * 10  # reserved
        data += self._build_matrix()  # matrix
        data += b'\x00' * 24  # pre_defined
        data += struct.pack('>I', 2)  # next_track_id
        
        return self.box(b'mvhd', data)
    
    def _build_matrix(self) -> bytes:
        """Build identity transformation matrix."""
        return struct.pack('>9I',
            0x00010000, 0, 0,
            0, 0x00010000, 0,
            0, 0, 0x40000000
        )
    
    def _build_trak(self, width: int, height: int, sps: bytes, pps: bytes) -> bytes:
        """Build Track Box (trak)."""
        tkhd = self._build_tkhd(width, height)
        mdia = self._build_mdia(width, height, sps, pps)
        
        return self.box(b'trak', tkhd + mdia)
    
    def _build_tkhd(self, width: int, height: int) -> bytes:
        """Build Track Header Box (tkhd)."""
        data = bytes([
            0x00,  # version
            0x00, 0x00, 0x03,  # flags (track enabled, in movie)
        ])
        data += struct.pack('>I', 0)  # creation_time
        data += struct.pack('>I', 0)  # modification_time
        data += struct.pack('>I', 1)  # track_id
        data += struct.pack('>I', 0)  # reserved
        data += struct.pack('>I', 0)  # duration
        data += b'\x00' * 8  # reserved
        data += struct.pack('>H', 0)  # layer
        data += struct.pack('>H', 0)  # alternate_group
        data += struct.pack('>H', 0)  # volume
        data += struct.pack('>H', 0)  # reserved
        data += self._build_matrix()  # matrix
        data += struct.pack('>I', width << 16)  # width (16.16 fixed point)
        data += struct.pack('>I', height << 16)  # height (16.16 fixed point)
        
        return self.box(b'tkhd', data)
    
    def _build_mdia(self, width: int, height: int, sps: bytes, pps: bytes) -> bytes:
        """Build Media Box (mdia)."""
        mdhd = self._build_mdhd()
        hdlr = self._build_hdlr()
        minf = self._build_minf(width, height, sps, pps)
        
        return self.box(b'mdia', mdhd + hdlr + minf)
    
    def _build_mdhd(self) -> bytes:
        """Build Media Header Box (mdhd)."""
        data = bytes([
            0x00,  # version
            0x00, 0x00, 0x00,  # flags
        ])
        data += struct.pack('>I', 0)  # creation_time
        data += struct.pack('>I', 0)  # modification_time
        data += struct.pack('>I', self.timescale)  # timescale
        data += struct.pack('>I', 0)  # duration
        data += struct.pack('>H', 0x55C4)  # language (und)
        data += struct.pack('>H', 0)  # pre_defined
        
        return self.box(b'mdhd', data)
    
    def _build_hdlr(self) -> bytes:
        """Build Handler Reference Box (hdlr)."""
        data = bytes([
            0x00,  # version
            0x00, 0x00, 0x00,  # flags
        ])
        data += struct.pack('>I', 0)  # pre_defined
        data += b'vide'  # handler_type (video)
        data += b'\x00' * 12  # reserved
        data += b'VideoHandler\x00'  # name
        
        return self.box(b'hdlr', data)
    
    def _build_minf(self, width: int, height: int, sps: bytes, pps: bytes) -> bytes:
        """Build Media Information Box (minf)."""
        vmhd = self._build_vmhd()
        dinf = self._build_dinf()
        stbl = self._build_stbl(width, height, sps, pps)
        
        return self.box(b'minf', vmhd + dinf + stbl)
    
    def _build_vmhd(self) -> bytes:
        """Build Video Media Header Box (vmhd)."""
        data = bytes([
            0x00,  # version
            0x00, 0x00, 0x01,  # flags
        ])
        data += struct.pack('>H', 0)  # graphicsmode
        data += struct.pack('>HHH', 0, 0, 0)  # opcolor
        
        return self.box(b'vmhd', data)
    
    def _build_dinf(self) -> bytes:
        """Build Data Information Box (dinf)."""
        dref = self._build_dref()
        return self.box(b'dinf', dref)
    
    def _build_dref(self) -> bytes:
        """Build Data Reference Box (dref)."""
        url = self.box(b'url ', bytes([0x00, 0x00, 0x00, 0x01]))  # self-contained
        
        data = bytes([
            0x00,  # version
            0x00, 0x00, 0x00,  # flags
        ])
        data += struct.pack('>I', 1)  # entry_count
        data += url
        
        return self.box(b'dref', data)
    
    def _build_stbl(self, width: int, height: int, sps: bytes, pps: bytes) -> bytes:
        """Build Sample Table Box (stbl)."""
        stsd = self._build_stsd(width, height, sps, pps)
        stts = self._build_stts()
        stsc = self._build_stsc()
        stsz = self._build_stsz()
        stco = self._build_stco()
        
        return self.box(b'stbl', stsd + stts + stsc + stsz + stco)
    
    def _build_stsd(self, width: int, height: int, sps: bytes, pps: bytes) -> bytes:
        """Build Sample Description Box (stsd)."""
        avc1 = self._build_avc1(width, height, sps, pps)
        
        data = bytes([
            0x00,  # version
            0x00, 0x00, 0x00,  # flags
        ])
        data += struct.pack('>I', 1)  # entry_count
        data += avc1
        
        return self.box(b'stsd', data)
    
    def _build_avc1(self, width: int, height: int, sps: bytes, pps: bytes) -> bytes:
        """Build AVC Sample Entry Box (avc1)."""
        avcc = self._build_avcc(sps, pps)
        
        data = b'\x00' * 6  # reserved
        data += struct.pack('>H', 1)  # data_reference_index
        data += b'\x00' * 16  # pre_defined + reserved
        data += struct.pack('>H', width)  # width
        data += struct.pack('>H', height)  # height
        data += struct.pack('>I', 0x00480000)  # horizresolution (72 dpi)
        data += struct.pack('>I', 0x00480000)  # vertresolution (72 dpi)
        data += struct.pack('>I', 0)  # reserved
        data += struct.pack('>H', 1)  # frame_count
        data += b'\x00' * 32  # compressorname
        data += struct.pack('>H', 0x0018)  # depth (24-bit)
        data += struct.pack('>h', -1)  # pre_defined
        data += avcc
        
        return self.box(b'avc1', data)
    
    def _build_avcc(self, sps: bytes, pps: bytes) -> bytes:
        """Build AVC Configuration Box (avcC)."""
        if not sps or len(sps) < 4:
            # Default profile/level
            profile = 0x64  # High Profile
            compat = 0x00
            level = 0x28  # Level 4.0
        else:
            profile = sps[1]
            compat = sps[2]
            level = sps[3]
        
        data = bytes([
            0x01,  # configurationVersion
            profile,  # AVCProfileIndication
            compat,  # profile_compatibility
            level,  # AVCLevelIndication
            0xFF,  # lengthSizeMinusOne (3 = 4 bytes)
        ])
        
        # SPS
        data += bytes([0xE1])  # numOfSequenceParameterSets
        data += struct.pack('>H', len(sps))
        data += sps
        
        # PPS
        data += bytes([0x01])  # numOfPictureParameterSets
        data += struct.pack('>H', len(pps))
        data += pps
        
        return self.box(b'avcC', data)
    
    def _build_stts(self) -> bytes:
        """Build Decoding Time to Sample Box (stts)."""
        data = bytes([0x00, 0x00, 0x00, 0x00])  # version + flags
        data += struct.pack('>I', 0)  # entry_count
        return self.box(b'stts', data)
    
    def _build_stsc(self) -> bytes:
        """Build Sample to Chunk Box (stsc)."""
        data = bytes([0x00, 0x00, 0x00, 0x00])  # version + flags
        data += struct.pack('>I', 0)  # entry_count
        return self.box(b'stsc', data)
    
    def _build_stsz(self) -> bytes:
        """Build Sample Size Box (stsz)."""
        data = bytes([0x00, 0x00, 0x00, 0x00])  # version + flags
        data += struct.pack('>I', 0)  # sample_size
        data += struct.pack('>I', 0)  # sample_count
        return self.box(b'stsz', data)
    
    def _build_stco(self) -> bytes:
        """Build Chunk Offset Box (stco)."""
        data = bytes([0x00, 0x00, 0x00, 0x00])  # version + flags
        data += struct.pack('>I', 0)  # entry_count
        return self.box(b'stco', data)
    
    def _build_mvex(self) -> bytes:
        """Build Movie Extends Box (mvex)."""
        trex = self._build_trex()
        return self.box(b'mvex', trex)
    
    def _build_trex(self) -> bytes:
        """Build Track Extends Box (trex)."""
        data = bytes([0x00, 0x00, 0x00, 0x00])  # version + flags
        data += struct.pack('>I', 1)  # track_id
        data += struct.pack('>I', 1)  # default_sample_description_index
        data += struct.pack('>I', 0)  # default_sample_duration
        data += struct.pack('>I', 0)  # default_sample_size
        data += struct.pack('>I', 0)  # default_sample_flags
        
        return self.box(b'trex', data)
    
    def build_init_segment(self, width: int, height: int, sps: bytes, pps: bytes) -> bytes:
        """
        Build complete init segment (ftyp + moov).
        
        Sent once when streaming starts.
        """
        ftyp = self.build_ftyp()
        moov = self.build_moov(width, height, sps, pps)
        return ftyp + moov
    
    def build_media_segment(self, nal_data: bytes, sequence_number: int,
                            decode_time: int, duration: int, 
                            is_keyframe: bool, sps: bytes = None, 
                            pps: bytes = None) -> bytes:
        """
        Build media segment (moof + mdat).
        
        Args:
            nal_data: NAL unit data (without start codes)
            sequence_number: Fragment sequence number
            decode_time: Base media decode time
            duration: Sample duration
            is_keyframe: True if this is an I-frame
            sps: SPS to prepend (for keyframes)
            pps: PPS to prepend (for keyframes)
        """
        # For keyframes, prepend SPS and PPS
        if is_keyframe and sps and pps:
            sps_with_length = struct.pack('>I', len(sps)) + sps
            pps_with_length = struct.pack('>I', len(pps)) + pps
            nal_with_length = sps_with_length + pps_with_length + struct.pack('>I', len(nal_data)) + nal_data
        else:
            nal_with_length = struct.pack('>I', len(nal_data)) + nal_data
        
        # Build moof
        moof = self._build_moof(sequence_number, decode_time, duration, 
                                len(nal_with_length), is_keyframe)
        
        # Build mdat
        mdat = self.box(b'mdat', nal_with_length)
        
        return moof + mdat
    
    def _build_moof(self, sequence_number: int, decode_time: int, 
                    duration: int, sample_size: int, is_keyframe: bool) -> bytes:
        """Build Movie Fragment Box (moof)."""
        mfhd = self._build_mfhd(sequence_number)
        traf = self._build_traf(decode_time, duration, sample_size, is_keyframe)
        
        return self.box(b'moof', mfhd + traf)
    
    def _build_mfhd(self, sequence_number: int) -> bytes:
        """Build Movie Fragment Header Box (mfhd)."""
        data = bytes([0x00, 0x00, 0x00, 0x00])  # version + flags
        data += struct.pack('>I', sequence_number)
        return self.box(b'mfhd', data)
    
    def _build_traf(self, decode_time: int, duration: int, 
                    sample_size: int, is_keyframe: bool) -> bytes:
        """Build Track Fragment Box (traf)."""
        tfhd = self._build_tfhd()
        tfdt = self._build_tfdt(decode_time)
        trun = self._build_trun(duration, sample_size, is_keyframe)
        
        return self.box(b'traf', tfhd + tfdt + trun)
    
    def _build_tfhd(self) -> bytes:
        """Build Track Fragment Header Box (tfhd)."""
        # flags: default-base-is-moof (0x020000)
        data = struct.pack('>I', 0x00020000)
        data += struct.pack('>I', 1)  # track_id
        return self.box(b'tfhd', data)
    
    def _build_tfdt(self, decode_time: int) -> bytes:
        """Build Track Fragment Decode Time Box (tfdt)."""
        data = bytes([0x00, 0x00, 0x00, 0x00])  # version 0
        data += struct.pack('>I', decode_time)
        return self.box(b'tfdt', data)
    
    def _build_trun(self, duration: int, sample_size: int, is_keyframe: bool) -> bytes:
        """Build Track Run Box (trun)."""
        # flags: data-offset, sample-duration, sample-size, sample-flags, sample-composition-time-offset
        flags = 0x00000F01
        
        # Sample flags
        if is_keyframe:
            sample_flags = 0x02000000  # is_sync
        else:
            sample_flags = 0x01010000  # depends on I-frame
        
        # Calculate data offset (moof size + mdat header)
        # This is a simplified calculation
        trun_size = 8 + 4 + 4 + 4 + 16  # box header + flags + count + offset + sample
        traf_size = 8 + 16 + 12 + trun_size  # tfhd + tfdt + trun (approx)
        moof_size = 8 + 16 + traf_size  # mfhd + traf
        data_offset = moof_size + 8  # +8 for mdat header
        
        data = struct.pack('>I', flags)
        data += struct.pack('>I', 1)  # sample_count
        data += struct.pack('>I', data_offset)
        data += struct.pack('>I', duration)
        data += struct.pack('>I', sample_size)
        data += struct.pack('>I', sample_flags)
        data += struct.pack('>I', 0)  # composition_time_offset
        
        return self.box(b'trun', data)
