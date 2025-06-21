"""Unified streaming VCD parser to replace BaseVCDParser.

This module provides a drop-in replacement for BaseVCDParser that uses
streaming architecture for better memory efficiency and performance.
"""

import mmap
import os
from typing import Optional, BinaryIO, Iterator, Dict, Any, Callable, List, Union
from collections import defaultdict
from pathlib import Path

from scoff.parsers.generic import ParserError
from hdltools.vcd.variable import VCDVariable
from hdltools.vcd.tokens import *
from hdltools.vcd.parser import (
    VCD_DEFINITION_LINES, VCD_VAR_LINES, END_PARSER,
    SCALAR_VALUE_CHANGE_PARSER, VECTOR_VALUE_CHANGE_PARSER, 
    REAL_VALUE_CHANGE_PARSER, SIM_TIME_PARSER, DUMPVARS_PARSER,
    SCOPE_PARSER, UPSCOPE_PARSER, VAR_PARSER
)


class StreamingVCDParser:
    """Unified streaming VCD parser.
    
    Drop-in replacement for BaseVCDParser with streaming capabilities,
    memory mapping support, and full API compatibility.
    """
    
    def __init__(self, chunk_size: int = 64 * 1024, use_mmap: bool = True, **kwargs):
        """Initialize streaming parser.
        
        Args:
            chunk_size: Size of chunks to read (default 64KB)
            use_mmap: Use memory mapping when possible
            **kwargs: Additional arguments (for compatibility)
        """
        # Core state (initialize first for mixin compatibility)
        self.chunk_size = chunk_size
        self.use_mmap = use_mmap
        self._debug = kwargs.get("debug", False)
        
        # Parser state
        self._current_state = "header"
        self._ticks = 0
        self._old_ticks = 0
        self._abort = False
        
        # Data structures (API compatibility)
        self._variables: Dict[str, VCDVariable] = {}
        self.timescale = None
        self.current_line = 0
        
        # State hooks (for mixin compatibility)
        self._state_hooks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Call parent __init__ for mixin compatibility (after our attrs are set)
        super().__init__(**kwargs)
        
        # Variable state tracking
        self._variable_values: Dict[str, str] = {}  # Current values
        self._scope_stack: List[str] = []
        
        # Streaming state
        self._file_handle: Optional[BinaryIO] = None
        self._mmap_handle: Optional[mmap.mmap] = None
        self._line_buffer = ""
        
    @property
    def current_time(self) -> int:
        """Get current simulation time."""
        return self._ticks
        
    @property
    def last_cycle_time(self) -> int:
        """Get last cycle time."""
        return self._old_ticks
        
    @property
    def variables(self) -> Dict[str, VCDVariable]:
        """Get variables dictionary (compatibility)."""
        # Check if mixin overrides this (like hierarchy mixin)
        if hasattr(self, '_vars') and self._vars is not self._variables:
            return self._vars
        return self._variables
        
    def add_state_hook(self, state: str, hook: Callable):
        """Add state change hook for mixin compatibility."""
        self._state_hooks[state].append(hook)
        
    def _abort_parser(self):
        """Abort parser (for early termination)."""
        self._abort = True
        
    def parse(self, data_or_filename: Union[str, bytes, Path]) -> None:
        """Parse VCD data with streaming.
        
        Args:
            data_or_filename: VCD data string, bytes, or filename
        """
        if isinstance(data_or_filename, (str, Path)):
            # File path - use streaming
            if isinstance(data_or_filename, Path):
                data_or_filename = str(data_or_filename)
            
            # Check if it's actually file content (compatibility)
            if '\n' in data_or_filename or data_or_filename.startswith('$'):
                # It's VCD content, not a filename
                self._parse_string_data(data_or_filename)
            else:
                # It's a filename
                self._parse_file_streaming(data_or_filename)
        else:
            # Bytes or string data
            if isinstance(data_or_filename, bytes):
                data_or_filename = data_or_filename.decode('utf-8', errors='ignore')
            self._parse_string_data(data_or_filename)
            
    def _parse_file_streaming(self, filename: str):
        """Parse file using streaming with memory mapping."""
        file_path = Path(filename)
        if not file_path.exists():
            raise FileNotFoundError(f"VCD file not found: {filename}")
            
        try:
            with open(filename, 'rb') as f:
                self._file_handle = f
                
                if self.use_mmap and os.path.getsize(filename) > self.chunk_size:
                    # Use memory mapping for large files
                    try:
                        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                            self._mmap_handle = mm
                            self._parse_mmap_streaming()
                    except (OSError, ValueError):
                        # Fall back to regular streaming
                        f.seek(0)
                        self._parse_file_chunks()
                else:
                    # Small file or mmap disabled - use chunk reading
                    self._parse_file_chunks()
        finally:
            self._file_handle = None
            self._mmap_handle = None
            
    def _parse_mmap_streaming(self):
        """Parse using memory-mapped file."""
        mm = self._mmap_handle
        mm.seek(0)
        
        while not self._abort:
            chunk = mm.read(self.chunk_size)
            if not chunk:
                break
                
            # Process chunk
            self._process_chunk(chunk.decode('utf-8', errors='ignore'))
            
        # Process any remaining buffer
        if self._line_buffer:
            self._process_line(self._line_buffer)
            
    def _parse_file_chunks(self):
        """Parse using chunked file reading."""
        f = self._file_handle
        
        while not self._abort:
            chunk = f.read(self.chunk_size)
            if not chunk:
                break
                
            # Process chunk
            chunk_str = chunk.decode('utf-8', errors='ignore')
            self._process_chunk(chunk_str)
            
        # Process any remaining buffer
        if self._line_buffer:
            self._process_line(self._line_buffer)
            
    def _parse_string_data(self, data: str):
        """Parse string data (compatibility mode)."""
        # Split into lines and process
        lines = data.split('\n')
        
        for line in lines:
            if self._abort:
                break
            self._process_line(line)
            self.current_line += 1
            
    def _process_chunk(self, chunk: str):
        """Process a chunk of data, handling line boundaries."""
        # Add to buffer
        self._line_buffer += chunk
        
        # Process complete lines
        while '\n' in self._line_buffer and not self._abort:
            line, self._line_buffer = self._line_buffer.split('\n', 1)
            self._process_line(line)
            self.current_line += 1
            
    def _process_line(self, line: str):
        """Process a single VCD line."""
        line = line.strip()
        if not line:
            return
            
        try:
            if self._current_state == "header":
                self._process_header_line(line)
            elif self._current_state == "initial":
                self._process_initial_line(line)
            elif self._current_state == "dump":
                self._process_dump_line(line)
        except Exception as e:
            if self._debug:
                print(f"DEBUG: Error processing line {self.current_line}: {line}")
                print(f"DEBUG: Error: {e}")
                raise
            else:
                # Continue parsing on errors for robustness
                pass
                
    def _process_header_line(self, line: str):
        """Process header section lines."""
        # Check for end of definitions
        if line == "$enddefinitions" or line.startswith("$enddefinitions"):
            self._change_state("initial")
            return
            
        # Parse header statements
        if line.startswith('$'):
            self._parse_header_statement(line)
        else:
            # Continuation of multi-line statement
            pass
            
    def _process_initial_line(self, line: str):
        """Process initial values section."""
        if line.startswith('#'):
            # Time change - move to dump section
            time = int(line[1:])
            self._advance_clock(time)
            self._change_state("dump")
            return
            
        # Initial value assignment
        self._parse_value_change(line, is_initial=True)
        
    def _process_dump_line(self, line: str):
        """Process dump section (main simulation data)."""
        if line.startswith('#'):
            # Time change
            time = int(line[1:])
            self._advance_clock(time)
        elif line.startswith('$dumpvars') or line.startswith('$dumpall'):
            # Dump statements - ignore
            pass
        else:
            # Value change
            self._parse_value_change(line)
            
    def _parse_header_statement(self, line: str):
        """Parse header statements like $var, $scope, etc."""
        if line.startswith('$var'):
            self._parse_variable_declaration(line)
        elif line.startswith('$scope'):
            self._parse_scope_start(line)
        elif line.startswith('$upscope'):
            self._parse_scope_end()
        elif line.startswith('$timescale'):
            self._parse_timescale(line)
        elif line.startswith('$date'):
            pass  # Ignore date
        elif line.startswith('$version'):
            pass  # Ignore version
        else:
            # Unknown header statement
            pass
            
        # Parse fields for compatibility
        fields = self._parse_statement_fields(line)
        
        # Call header handler for compatibility
        self.header_statement_handler(line, fields)
        
        # Call state hooks for mixins (like hierarchy)
        stmt_type = self._get_statement_type(line)
        for hook in self._state_hooks.get("header", []):
            try:
                hook("header", stmt_type, fields)
            except Exception as e:
                if self._debug:
                    print(f"DEBUG: Hook error: {e}")
        
    def _parse_variable_declaration(self, line: str):
        """Parse $var statement."""
        parts = line.split()
        if len(parts) >= 5:
            var_type = parts[1]
            width = int(parts[2])
            var_id = parts[3]
            name = parts[4]
            
            # Create variable (check if mixin handles this)
            if hasattr(self, '_vars'):
                # Hierarchy mixin will handle variable creation via header handler
                # Just initialize our tracking
                self._variable_values[var_id] = '0'
            else:
                # No mixin - handle it ourselves
                var = VCDVariable(var_id, name, var_type, width)
                var.scope = self._scope_stack.copy()
                var.reference = '.'.join(self._scope_stack + [name])
                var.value = '0'  # Default value
                
                self._variables[var_id] = var
                self._variable_values[var_id] = '0'
            
    def _parse_scope_start(self, line: str):
        """Parse $scope statement."""
        parts = line.split()
        if len(parts) >= 3:
            scope_name = parts[2]
            self._scope_stack.append(scope_name)
            
    def _parse_scope_end(self):
        """Parse $upscope statement."""
        if self._scope_stack:
            self._scope_stack.pop()
            
    def _parse_timescale(self, line: str):
        """Parse $timescale statement."""
        # Extract timescale value
        if '$end' in line:
            # Single line: $timescale 1ns $end
            parts = line.split()
            if len(parts) >= 2:
                self.timescale = parts[1]
        else:
            # Multi-line format - will be in next line
            pass
            
    def _parse_value_change(self, line: str, is_initial: bool = False):
        """Parse value change statements."""
        if not line:
            return
            
        var_id = None
        value = None
        
        # Scalar value change: 0a, 1b, xa, etc.
        if len(line) >= 2 and line[0] in '01xzXZ':
            value = line[0]
            var_id = line[1:]
            
        # Vector value change: b0101 var_id
        elif line.startswith('b') or line.startswith('r'):
            parts = line.split()
            if len(parts) >= 2:
                value = parts[0][1:]  # Remove 'b' or 'r' prefix
                var_id = parts[1]
                
        if var_id and var_id in self._variables:
            # Update variable value
            old_value = self._variable_values.get(var_id, '0')
            self._variable_values[var_id] = value
            
            # Update variable object
            var = self._variables[var_id]
            var.value = value
            var.last_changed = self._ticks
            
            # Call handler
            fields = {'var': var_id, 'value': value}
            if is_initial:
                self.initial_value_handler(line, fields)
            else:
                self.value_change_handler(line, fields)
                
    def _parse_statement_fields(self, line: str) -> Dict[str, Any]:
        """Parse statement into fields (for compatibility)."""
        # Simple field extraction for compatibility
        fields = {}
        parts = line.split()
        
        if line.startswith('$timescale') and len(parts) >= 2:
            fields['timescale'] = parts[1]
        elif line.startswith('$var') and len(parts) >= 5:
            fields['vtype'] = parts[1]
            fields['width'] = int(parts[2])
            fields['id'] = parts[3]
            fields['name'] = parts[4]
        elif line.startswith('$scope') and len(parts) >= 3:
            fields['stype'] = parts[1]
            fields['sname'] = parts[2]
            
        return fields
        
    def _get_statement_type(self, line: str):
        """Get statement type object for mixin compatibility."""
        # Import the parser objects that mixins expect
        if line.startswith('$var'):
            return VAR_PARSER
        elif line.startswith('$scope'):
            return SCOPE_PARSER
        elif line.startswith('$upscope'):
            return UPSCOPE_PARSER
        else:
            return None
        
    def _advance_clock(self, new_time: int):
        """Advance simulation time."""
        self._old_ticks = self._ticks
        self._ticks = new_time
        self.clock_change_handler(new_time)
        
    def _change_state(self, new_state: str):
        """Change parser state and trigger hooks."""
        old_state = self._current_state
        self._current_state = new_state
        
        # Call state change handler
        self._state_change_handler(old_state, new_state)
        
        # Call state hooks
        for hook in self._state_hooks.get(new_state, []):
            try:
                hook()
            except Exception as e:
                if self._debug:
                    print(f"DEBUG: State hook error: {e}")
                    
    # Handler methods (must be overridden by subclasses)
    def header_statement_handler(self, stmt, fields):
        """Handle header statement."""
        pass
        
    def initial_value_handler(self, stmt, fields):
        """Handle initial value assignment."""
        pass
        
    def value_change_handler(self, stmt, fields):
        """Handle value change."""
        pass
        
    def clock_change_handler(self, time):
        """Handle clock change."""
        pass
        
    def _state_change_handler(self, old_state, new_state):
        """Handle state transition."""
        pass
        
    # Compatibility methods for existing tools
    def variable_search(self, name: str, scope: Optional[str] = None, 
                       aliases: bool = True) -> List[VCDVariable]:
        """Search for variables by name/scope (hierarchy mixin compatibility)."""
        results = []
        
        for var in self._variables.values():
            if scope:
                if scope not in var.reference:
                    continue
                    
            if name in var.name or name in var.reference:
                results.append(var)
                
        return results


# Note: BaseVCDParser compatibility is handled by parser.py lazy loader