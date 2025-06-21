"""Efficient binary storage for VCD signal values.

This module provides high-performance binary storage for VCD signals,
replacing the inefficient string-based approach with indexed binary data.
"""

import struct
from typing import Dict, List, Optional, Tuple, Union
from enum import IntEnum
import bisect
from collections import defaultdict


class SignalState(IntEnum):
    """Binary representation of VCD signal states."""
    ZERO = 0b00    # '0'
    ONE = 0b01     # '1' 
    UNKNOWN = 0b10 # 'x' or 'X'
    HIGHZ = 0b11   # 'z' or 'Z'


class BinarySignalValue:
    """Efficient binary storage for multi-bit signal values."""
    
    def __init__(self, width: int, value: Union[str, int, bytes] = None):
        """Initialize binary signal value.
        
        Args:
            width: Bit width of the signal
            value: Initial value (string like "b1010", integer, or bytes)
        """
        self.width = width
        # Pack into bytes - 4 states per byte (2 bits each)
        self._packed_bytes = bytearray((width + 3) // 4)
        
        if value is not None:
            self.set_value(value)
    
    def set_value(self, value: Union[str, int, bytes]):
        """Set signal value efficiently."""
        if isinstance(value, str):
            self._set_from_string(value)
        elif isinstance(value, int):
            self._set_from_int(value)
        elif isinstance(value, bytes):
            self._packed_bytes = bytearray(value)
        else:
            raise ValueError(f"Unsupported value type: {type(value)}")
    
    def _set_from_string(self, value_str: str):
        """Convert VCD string representation to binary."""
        # Remove VCD prefixes
        if value_str.startswith('b'):
            binary_str = value_str[1:]
            base = 2
        elif value_str.startswith('h'):
            binary_str = bin(int(value_str[1:], 16))[2:]
            base = 2
        elif value_str.startswith('o'):
            binary_str = bin(int(value_str[1:], 8))[2:]
            base = 2
        else:
            binary_str = value_str
            base = 2
        
        # Pad to width
        binary_str = binary_str.zfill(self.width)
        
        # Pack 4 states per byte (2 bits each)
        self._packed_bytes = bytearray((self.width + 3) // 4)
        
        for i, char in enumerate(reversed(binary_str)):
            if char == '0':
                state = SignalState.ZERO
            elif char == '1':
                state = SignalState.ONE
            elif char.lower() == 'x':
                state = SignalState.UNKNOWN
            elif char.lower() == 'z':
                state = SignalState.HIGHZ
            else:
                state = SignalState.UNKNOWN
            
            byte_idx = i // 4
            bit_idx = (i % 4) * 2
            
            # Clear existing bits and set new state
            self._packed_bytes[byte_idx] &= ~(0b11 << bit_idx)
            self._packed_bytes[byte_idx] |= (state << bit_idx)
    
    def _set_from_int(self, value: int):
        """Set from integer value (assumes binary)."""
        binary_str = format(value, f'0{self.width}b')
        self._set_from_string(binary_str)
    
    def get_bit(self, index: int) -> SignalState:
        """Get state of specific bit."""
        if index >= self.width:
            raise IndexError(f"Bit index {index} out of range for width {self.width}")
        
        byte_idx = index // 4
        bit_idx = (index % 4) * 2
        
        return SignalState((self._packed_bytes[byte_idx] >> bit_idx) & 0b11)
    
    def to_int(self) -> Optional[int]:
        """Convert to integer if all bits are 0/1, None if X/Z present."""
        result = 0
        for i in range(self.width):
            state = self.get_bit(i)
            if state == SignalState.ZERO:
                pass  # Bit remains 0
            elif state == SignalState.ONE:
                result |= (1 << i)
            else:
                return None  # Unknown or high-Z state
        return result
    
    def to_string(self, format_type: str = 'b') -> str:
        """Convert to VCD string representation."""
        if format_type == 'b':
            # Binary format
            chars = []
            for i in range(self.width - 1, -1, -1):
                state = self.get_bit(i)
                if state == SignalState.ZERO:
                    chars.append('0')
                elif state == SignalState.ONE:
                    chars.append('1')
                elif state == SignalState.UNKNOWN:
                    chars.append('x')
                else:  # HIGH_Z
                    chars.append('z')
            return 'b' + ''.join(chars)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def __eq__(self, other):
        """Efficient equality comparison."""
        if not isinstance(other, BinarySignalValue):
            return False
        return (self.width == other.width and 
                self._packed_bytes == other._packed_bytes)
    
    def __hash__(self):
        """Hash for use in sets/dicts."""
        return hash((self.width, bytes(self._packed_bytes)))


class TimeIndexedHistory:
    """Time-indexed signal history with O(log n) lookups."""
    
    def __init__(self):
        """Initialize empty history."""
        self._times: List[int] = []           # Sorted list of times
        self._values: List[BinarySignalValue] = []  # Corresponding values
        self._time_to_index: Dict[int, int] = {}    # Time -> index mapping
    
    def add_change(self, time: int, value: BinarySignalValue):
        """Add a value change at specific time."""
        # Use binary search for insertion point
        idx = bisect.bisect_left(self._times, time)
        
        if idx < len(self._times) and self._times[idx] == time:
            # Update existing time point
            self._values[idx] = value
        else:
            # Insert new time point
            self._times.insert(idx, time)
            self._values.insert(idx, value)
            
            # Update index mapping for all following entries
            for i in range(idx, len(self._times)):
                self._time_to_index[self._times[i]] = i
    
    def get_value_at(self, time: int) -> Optional[BinarySignalValue]:
        """Get value at specific time - O(log n) lookup."""
        if not self._times:
            return None
        
        # Binary search for time or last value before time
        idx = bisect.bisect_right(self._times, time) - 1
        
        if idx >= 0:
            return self._values[idx]
        return None
    
    def get_changes_in_range(self, start_time: int, end_time: int) -> List[Tuple[int, BinarySignalValue]]:
        """Get all changes in time range - O(log n + k) where k is result size."""
        start_idx = bisect.bisect_left(self._times, start_time)
        end_idx = bisect.bisect_right(self._times, end_time)
        
        return [(self._times[i], self._values[i]) 
                for i in range(start_idx, end_idx)]
    
    def get_all_changes(self) -> List[Tuple[int, BinarySignalValue]]:
        """Get all changes in chronological order."""
        return list(zip(self._times, self._values))
    
    def __len__(self) -> int:
        """Number of value changes."""
        return len(self._times)


class VariableIndex:
    """Hierarchical index for fast variable lookups."""
    
    def __init__(self):
        """Initialize empty index."""
        self._scope_index: Dict[str, List[str]] = defaultdict(list)  # scope -> var_ids
        self._name_index: Dict[str, List[str]] = defaultdict(list)   # name -> var_ids
        self._full_path_index: Dict[str, str] = {}                   # full_path -> var_id
    
    def add_variable(self, var_id: str, name: str, scope_path: List[str]):
        """Add variable to index."""
        # Add to name index
        self._name_index[name].append(var_id)
        
        # Add to scope indices
        full_scope = '.'.join(scope_path)
        self._scope_index[full_scope].append(var_id)
        
        # Add partial scope paths
        for i in range(len(scope_path)):
            partial_scope = '.'.join(scope_path[:i+1])
            self._scope_index[partial_scope].append(var_id)
        
        # Add full path
        full_path = '.'.join(scope_path + [name])
        self._full_path_index[full_path] = var_id
    
    def find_by_name(self, name: str) -> List[str]:
        """Find variables by name - O(1) lookup."""
        return self._name_index.get(name, [])
    
    def find_by_scope(self, scope: str) -> List[str]:
        """Find variables in scope - O(1) lookup."""
        return self._scope_index.get(scope, [])
    
    def find_by_pattern(self, pattern: str) -> List[str]:
        """Find variables matching pattern (supports wildcards)."""
        import fnmatch
        results = []
        
        for full_path, var_id in self._full_path_index.items():
            if fnmatch.fnmatch(full_path, pattern):
                results.append(var_id)
        
        return results


class EfficientVCDStorage:
    """High-performance VCD data storage with binary values and indexing."""
    
    def __init__(self):
        """Initialize efficient storage."""
        self.variables: Dict[str, 'EfficientVCDVariable'] = {}
        self.variable_index = VariableIndex()
        self._conversion_cache: Dict[str, BinarySignalValue] = {}
    
    def add_variable(self, var_id: str, name: str, var_type: str, 
                    width: int, scope_path: List[str]):
        """Add a variable to the efficient storage."""
        var = EfficientVCDVariable(var_id, name, var_type, width, scope_path)
        self.variables[var_id] = var
        self.variable_index.add_variable(var_id, name, scope_path)
        return var
    
    def set_value(self, var_id: str, time: int, value: Union[str, BinarySignalValue]):
        """Set variable value with caching."""
        if var_id not in self.variables:
            return
        
        var = self.variables[var_id]
        
        # Use cached conversion if available
        if isinstance(value, str):
            cache_key = f"{var.width}:{value}"
            if cache_key in self._conversion_cache:
                binary_value = self._conversion_cache[cache_key]
            else:
                binary_value = BinarySignalValue(var.width, value)
                self._conversion_cache[cache_key] = binary_value
        else:
            binary_value = value
        
        var.history.add_change(time, binary_value)
        var.current_value = binary_value
    
    def get_value(self, var_id: str, time: Optional[int] = None) -> Optional[BinarySignalValue]:
        """Get variable value at time (current if time=None)."""
        if var_id not in self.variables:
            return None
        
        var = self.variables[var_id]
        if time is None:
            return var.current_value
        else:
            return var.history.get_value_at(time)
    
    def find_variables(self, name: str = None, scope: str = None, 
                      pattern: str = None) -> List['EfficientVCDVariable']:
        """Find variables using indexed lookups."""
        if pattern:
            var_ids = self.variable_index.find_by_pattern(pattern)
        elif name and scope:
            name_ids = set(self.variable_index.find_by_name(name))
            scope_ids = set(self.variable_index.find_by_scope(scope))
            var_ids = list(name_ids & scope_ids)
        elif name:
            var_ids = self.variable_index.find_by_name(name)
        elif scope:
            var_ids = self.variable_index.find_by_scope(scope)
        else:
            var_ids = list(self.variables.keys())
        
        return [self.variables[var_id] for var_id in var_ids 
                if var_id in self.variables]


class EfficientVCDVariable:
    """Efficient VCD variable with binary storage and indexed history."""
    
    def __init__(self, var_id: str, name: str, var_type: str, 
                 width: int, scope_path: List[str]):
        """Initialize efficient variable."""
        self.id = var_id
        self.name = name
        self.type = var_type
        self.width = width
        self.scope_path = scope_path
        self.reference = '.'.join(scope_path + [name])
        
        # Efficient storage
        self.history = TimeIndexedHistory()
        self.current_value: Optional[BinarySignalValue] = None
        self.last_changed: int = 0
    
    def get_value_at(self, time: int) -> Optional[BinarySignalValue]:
        """Get value at specific time."""
        return self.history.get_value_at(time)
    
    def get_changes_in_range(self, start_time: int, end_time: int) -> List[Tuple[int, BinarySignalValue]]:
        """Get changes in time range."""
        return self.history.get_changes_in_range(start_time, end_time)
    
    def __repr__(self):
        """String representation."""
        return f"EfficientVCDVariable(id='{self.id}', name='{self.name}', width={self.width})"