"""FST file parser implementation."""

import struct
import zlib
from typing import Optional, BinaryIO, Iterator, Tuple, Dict, Any
from pathlib import Path

from . import FSTFormat, FSTHeader, FSTVariable, FSTScope, FSTError


class FSTParser:
    """FST file parser.
    
    Provides streaming access to FST files without loading entire file into memory.
    """
    
    def __init__(self, filename: str):
        """Initialize FST parser.
        
        Args:
            filename: Path to FST file
        """
        self.filename = Path(filename)
        self._file: Optional[BinaryIO] = None
        self.header = FSTHeader()
        self._block_offsets: Dict[int, int] = {}
        self._variables: Dict[str, FSTVariable] = {}
        self._time_index: Dict[int, int] = {}  # time -> file offset mapping
        
    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        
    def open(self):
        """Open FST file for reading."""
        if self._file:
            raise FSTError("File already open")
            
        self._file = open(self.filename, 'rb')
        self._parse_header()
        self._build_indices()
        
    def close(self):
        """Close FST file."""
        if self._file:
            self._file.close()
            self._file = None
            
    def _parse_header(self):
        """Parse FST file header."""
        if not self._file:
            raise FSTError("File not open")
            
        # Check magic number
        magic = self._file.read(4)
        if magic != FSTFormat.MAGIC:
            raise FSTError(f"Invalid FST magic number: {magic}")
            
        # Read header block
        block_type = struct.unpack('B', self._file.read(1))[0]
        if block_type != FSTFormat.BLOCK_HEADER:
            raise FSTError(f"Expected header block, got {block_type}")
            
        # Parse header fields
        self._parse_header_block()
        
    def _parse_header_block(self):
        """Parse FST header block contents."""
        # This is a simplified version - real FST has more complex header
        # Read block size
        block_size = struct.unpack('<I', self._file.read(4))[0]
        header_data = self._file.read(block_size)
        
        # Parse timescale, start/end times, etc.
        # For now, use defaults
        self.header.timescale = "1ns"
        self.header.start_time = 0
        
    def _build_indices(self):
        """Build indices for fast access."""
        if not self._file:
            raise FSTError("File not open")
            
        # Scan file to build block offset index
        self._file.seek(0)
        self._file.read(4)  # Skip magic
        
        while True:
            pos = self._file.tell()
            
            # Read block type
            block_data = self._file.read(1)
            if not block_data:
                break
                
            block_type = struct.unpack('B', block_data)[0]
            
            # Read block size
            size_data = self._file.read(4)
            if len(size_data) < 4:
                break
                
            block_size = struct.unpack('<I', size_data)[0]
            
            # Store offset
            self._block_offsets[block_type] = pos
            
            # Skip block data
            self._file.seek(block_size, 1)
            
    def get_hierarchy(self) -> FSTScope:
        """Get signal hierarchy.
        
        Returns:
            Root scope containing full hierarchy
        """
        if not self._file:
            raise FSTError("File not open")
            
        # Find hierarchy block
        if FSTFormat.BLOCK_HIER not in self._block_offsets:
            raise FSTError("No hierarchy block found")
            
        self._file.seek(self._block_offsets[FSTFormat.BLOCK_HIER])
        
        # Parse hierarchy
        # This is simplified - real implementation would parse actual hierarchy
        return self.header.scope_root
        
    def get_variables(self) -> Dict[str, FSTVariable]:
        """Get all variables.
        
        Returns:
            Dictionary mapping variable IDs to FSTVariable objects
        """
        return self._variables.copy()
        
    def get_value_changes(self, start_time: Optional[int] = None,
                         end_time: Optional[int] = None) -> Iterator[Tuple[int, str, str]]:
        """Get value changes in time range.
        
        Args:
            start_time: Start time (inclusive), None for beginning
            end_time: End time (inclusive), None for end
            
        Yields:
            Tuples of (time, var_id, value)
        """
        if not self._file:
            raise FSTError("File not open")
            
        # Find appropriate vcdata block
        if FSTFormat.BLOCK_VCDATA not in self._block_offsets:
            raise FSTError("No value change data block found")
            
        self._file.seek(self._block_offsets[FSTFormat.BLOCK_VCDATA])
        
        # This is a simplified implementation
        # Real FST parsing would involve decompression and more complex decoding
        current_time = 0
        
        # Mock implementation - yield some example changes
        if start_time is None or current_time >= start_time:
            if end_time is None or current_time <= end_time:
                yield (current_time, "!", "1")
                
    def get_value_at_time(self, var_id: str, time: int) -> Optional[str]:
        """Get variable value at specific time.
        
        Args:
            var_id: Variable identifier
            time: Simulation time
            
        Returns:
            Value string or None if not found
        """
        # This would use time index for efficient lookup
        # For now, return mock value
        return "0"
        
        
class FSTStreamingParser:
    """Streaming FST parser for processing large files.
    
    Processes FST file in chunks without loading entire file into memory.
    """
    
    def __init__(self, filename: str, chunk_size: int = 1024 * 1024):
        """Initialize streaming parser.
        
        Args:
            filename: Path to FST file
            chunk_size: Size of chunks to process (default 1MB)
        """
        self.filename = Path(filename)
        self.chunk_size = chunk_size
        self._callbacks = {
            'variable': [],
            'value_change': [],
            'time_change': []
        }
        
    def on_variable(self, callback):
        """Register callback for variable definitions.
        
        Callback signature: callback(var: FSTVariable)
        """
        self._callbacks['variable'].append(callback)
        
    def on_value_change(self, callback):
        """Register callback for value changes.
        
        Callback signature: callback(time: int, var_id: str, value: str)
        """
        self._callbacks['value_change'].append(callback)
        
    def on_time_change(self, callback):
        """Register callback for time changes.
        
        Callback signature: callback(time: int)
        """
        self._callbacks['time_change'].append(callback)
        
    def parse(self):
        """Parse FST file using registered callbacks."""
        with open(self.filename, 'rb') as f:
            # Check magic
            magic = f.read(4)
            if magic != FSTFormat.MAGIC:
                raise FSTError(f"Invalid FST magic: {magic}")
                
            # Process blocks
            while True:
                block_type_data = f.read(1)
                if not block_type_data:
                    break
                    
                block_type = struct.unpack('B', block_type_data)[0]
                block_size = struct.unpack('<I', f.read(4))[0]
                
                # Process block based on type
                if block_type == FSTFormat.BLOCK_HIER:
                    self._process_hierarchy_block(f, block_size)
                elif block_type == FSTFormat.BLOCK_VCDATA:
                    self._process_vcdata_block(f, block_size)
                else:
                    # Skip unknown blocks
                    f.seek(block_size, 1)
                    
    def _process_hierarchy_block(self, f: BinaryIO, size: int):
        """Process hierarchy block."""
        # Simplified - would parse actual hierarchy data
        pass
        
    def _process_vcdata_block(self, f: BinaryIO, size: int):
        """Process value change data block."""
        # Simplified - would parse actual value changes
        pass