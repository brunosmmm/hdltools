"""FST file generator implementation."""

import struct
import zlib
from typing import BinaryIO, Dict, List, Optional, Tuple
from pathlib import Path
import time

from . import FSTFormat, FSTHeader, FSTVariable, FSTScope, FSTError


class FSTGenerator:
    """FST file generator.
    
    Generates FST files from simulation data with efficient compression.
    """
    
    def __init__(self, filename: str, timescale: str = "1ns"):
        """Initialize FST generator.
        
        Args:
            filename: Output FST filename
            timescale: Time unit (default "1ns")
        """
        self.filename = Path(filename)
        self.timescale = timescale
        self._file: Optional[BinaryIO] = None
        self._variables: Dict[str, FSTVariable] = {}
        self._scopes: List[FSTScope] = []
        self._current_time = 0
        self._value_buffer: List[Tuple[int, str, str]] = []
        self._buffer_size = 1024 * 1024  # 1MB buffer
        
    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        
    def open(self):
        """Open FST file for writing."""
        if self._file:
            raise FSTError("File already open")
            
        self._file = open(self.filename, 'wb')
        self._write_magic()
        
    def close(self):
        """Close FST file and write final data."""
        if self._file:
            # Flush any remaining buffered data
            self._flush_value_buffer()
            
            # Write end marker
            self._write_end_marker()
            
            self._file.close()
            self._file = None
            
    def _write_magic(self):
        """Write FST magic number."""
        self._file.write(FSTFormat.MAGIC)
        
    def _write_end_marker(self):
        """Write end of file marker."""
        # FST uses specific end markers
        self._file.write(b'\xFF')
        
    def add_scope(self, scope_path: List[str], scope_type: str = "module") -> FSTScope:
        """Add a scope (module/interface) to hierarchy.
        
        Args:
            scope_path: List of scope names from root
            scope_type: Type of scope (default "module")
            
        Returns:
            Created scope object
        """
        scope = FSTScope(scope_path[-1], scope_type)
        self._scopes.append(scope)
        return scope
        
    def add_variable(self, var_id: str, name: str, var_type: str,
                    width: int, scope_path: List[str]) -> FSTVariable:
        """Add a variable to the FST file.
        
        Args:
            var_id: Unique variable identifier
            name: Variable name
            var_type: Variable type (wire, reg, etc.)
            width: Bit width
            scope_path: Scope hierarchy path
            
        Returns:
            Created variable object
        """
        if var_id in self._variables:
            raise FSTError(f"Variable {var_id} already exists")
            
        var = FSTVariable(var_id, name, var_type, width, scope_path)
        self._variables[var_id] = var
        return var
        
    def write_header(self):
        """Write FST header with hierarchy information."""
        if not self._file:
            raise FSTError("File not open")
            
        # Write header block
        self._file.write(struct.pack('B', FSTFormat.BLOCK_HEADER))
        
        # Build header data
        header_data = bytearray()
        
        # Add timescale
        header_data.extend(self.timescale.encode('utf-8'))
        header_data.append(0)  # Null terminator
        
        # Add date
        date_str = time.strftime("%c")
        header_data.extend(date_str.encode('utf-8'))
        header_data.append(0)
        
        # Write header size and data
        self._file.write(struct.pack('<I', len(header_data)))
        self._file.write(header_data)
        
        # Write hierarchy block
        self._write_hierarchy()
        
    def _write_hierarchy(self):
        """Write hierarchy block."""
        self._file.write(struct.pack('B', FSTFormat.BLOCK_HIER))
        
        # Build hierarchy data
        hier_data = bytearray()
        
        # Add scopes and variables
        # This is simplified - real FST has more complex encoding
        for var in self._variables.values():
            # Variable type byte
            var_type_map = {
                'wire': FSTFormat.VAR_TYPE_WIRE,
                'reg': FSTFormat.VAR_TYPE_REG,
                'integer': FSTFormat.VAR_TYPE_INTEGER,
                'real': FSTFormat.VAR_TYPE_REAL,
            }
            hier_data.append(var_type_map.get(var.type, FSTFormat.VAR_TYPE_WIRE))
            
            # Variable data
            var_info = f"{var.id}:{var.width}:{var.name}".encode('utf-8')
            hier_data.extend(var_info)
            hier_data.append(0)
            
        # Write hierarchy size and data
        self._file.write(struct.pack('<I', len(hier_data)))
        self._file.write(hier_data)
        
    def set_time(self, new_time: int):
        """Set current simulation time.
        
        Args:
            new_time: New simulation time
        """
        if new_time < self._current_time:
            raise FSTError(f"Time cannot go backwards: {new_time} < {self._current_time}")
            
        self._current_time = new_time
        
    def add_value_change(self, var_id: str, value: str):
        """Add a value change at current time.
        
        Args:
            var_id: Variable identifier
            value: New value
        """
        if var_id not in self._variables:
            raise FSTError(f"Unknown variable: {var_id}")
            
        self._value_buffer.append((self._current_time, var_id, value))
        
        # Flush buffer if it's getting large
        if len(self._value_buffer) >= self._buffer_size:
            self._flush_value_buffer()
            
    def _flush_value_buffer(self):
        """Flush value buffer to file."""
        if not self._value_buffer:
            return
            
        # Write value change data block
        self._file.write(struct.pack('B', FSTFormat.BLOCK_VCDATA))
        
        # Build value change data
        vc_data = bytearray()
        
        # Group changes by time
        time_groups: Dict[int, List[Tuple[str, str]]] = {}
        for time, var_id, value in self._value_buffer:
            if time not in time_groups:
                time_groups[time] = []
            time_groups[time].append((var_id, value))
            
        # Write time-grouped changes
        for time in sorted(time_groups.keys()):
            # Write time using variable-length encoding
            vc_data.extend(FSTFormat.encode_time(time))
            
            # Write number of changes at this time
            changes = time_groups[time]
            vc_data.append(len(changes))
            
            # Write each change
            for var_id, value in changes:
                # Encode variable ID and value
                # This is simplified - real FST uses more complex encoding
                change_data = f"{var_id}:{value}".encode('utf-8')
                vc_data.extend(change_data)
                vc_data.append(0)
                
        # Compress data
        compressed = zlib.compress(vc_data)
        
        # Write size and compressed data
        self._file.write(struct.pack('<I', len(compressed)))
        self._file.write(compressed)
        
        # Clear buffer
        self._value_buffer.clear()
        

class FSTStreamingGenerator:
    """Streaming FST generator for creating large FST files efficiently."""
    
    def __init__(self, filename: str, timescale: str = "1ns",
                 compress_level: int = 6):
        """Initialize streaming generator.
        
        Args:
            filename: Output filename
            timescale: Time unit
            compress_level: Compression level (0-9)
        """
        self.filename = Path(filename)
        self.timescale = timescale
        self.compress_level = compress_level
        self._generator = FSTGenerator(filename, timescale)
        
    def __enter__(self):
        """Context manager entry."""
        self._generator.open()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._generator.close()
        
    def add_variable(self, var_id: str, name: str, var_type: str,
                    width: int, scope_path: List[str]):
        """Add variable definition."""
        return self._generator.add_variable(var_id, name, var_type, width, scope_path)
        
    def write_header(self):
        """Write file header."""
        self._generator.write_header()
        
    def write_time_block(self, time: int, changes: List[Tuple[str, str]]):
        """Write all changes for a specific time.
        
        Args:
            time: Simulation time
            changes: List of (var_id, value) tuples
        """
        self._generator.set_time(time)
        for var_id, value in changes:
            self._generator.add_value_change(var_id, value)