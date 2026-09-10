"""FST (Fast Signal Trace) format support for hdltools.

FST is a compressed binary waveform format used by GtkWave for efficient
storage and access of large simulation traces.
"""

from typing import Optional, List, Dict, Any
import struct
from pathlib import Path


class FSTVariable:
    """FST variable representation."""
    
    def __init__(self, var_id: str, name: str, var_type: str, 
                 width: int, scope: List[str]):
        """Initialize FST variable."""
        self.id = var_id
        self.name = name
        self.type = var_type
        self.width = width
        self.scope = scope
        self.alias = None
        
    @property
    def full_name(self) -> str:
        """Get full hierarchical name."""
        return ".".join(self.scope + [self.name])


class FSTScope:
    """FST scope (module/interface) representation."""
    
    def __init__(self, name: str, scope_type: str):
        """Initialize scope."""
        self.name = name
        self.type = scope_type
        self.children = []
        self.variables = []
        
    def add_child(self, child: "FSTScope"):
        """Add child scope."""
        self.children.append(child)
        
    def add_variable(self, var: FSTVariable):
        """Add variable to scope."""
        self.variables.append(var)


class FSTHeader:
    """FST file header information."""
    
    def __init__(self):
        """Initialize header."""
        self.date = ""
        self.version = ""
        self.timescale = "1ns"
        self.scope_root = FSTScope("$root", "module")
        self.start_time = 0
        self.end_time = 0
        
        
class FSTFormat:
    """FST format constants and utilities."""
    
    # FST magic number
    MAGIC = b'FST\x00'
    
    # Block types
    BLOCK_HEADER = 0x01
    BLOCK_VCDATA = 0x02
    BLOCK_BLACKOUT = 0x03
    BLOCK_GEOM = 0x04
    BLOCK_HIER = 0x05
    BLOCK_VCDATA_DYN_ALIAS = 0x06
    BLOCK_HIER_LZ4 = 0x07
    BLOCK_VCDATA_LZ4 = 0x08
    BLOCK_VCDATA_DYN_ALIAS_LZ4 = 0x09
    
    # Variable types
    VAR_TYPE_WIRE = 0x00
    VAR_TYPE_REG = 0x01
    VAR_TYPE_INTEGER = 0x02
    VAR_TYPE_REAL = 0x03
    VAR_TYPE_PARAMETER = 0x04
    VAR_TYPE_STRING = 0x05
    
    @staticmethod
    def encode_time(time: int) -> bytes:
        """Encode time value using FST variable-length encoding."""
        # FST uses variable-length encoding for time values
        result = bytearray()
        while time >= 0x80:
            result.append((time & 0x7F) | 0x80)
            time >>= 7
        result.append(time & 0x7F)
        return bytes(result)
    
    @staticmethod
    def decode_time(data: bytes, offset: int = 0) -> tuple[int, int]:
        """Decode FST variable-length time value.
        
        Returns:
            Tuple of (time_value, bytes_consumed)
        """
        time = 0
        shift = 0
        consumed = 0
        
        while offset + consumed < len(data):
            byte = data[offset + consumed]
            time |= (byte & 0x7F) << shift
            consumed += 1
            
            if byte & 0x80 == 0:
                break
                
            shift += 7
            
        return time, consumed


class FSTError(Exception):
    """FST format error."""
    pass