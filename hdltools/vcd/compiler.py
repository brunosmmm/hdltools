"""VCD to compact representation compiler."""

import pickle
from hdltools.vcd import VCDObject
from hdltools.vcd.streaming_parser import StreamingVCDParser
from hdltools.vcd.mixins.hierarchy import VCDHierarchyAnalysisMixin
try:
    from hdltools.vcd.efficient_storage import EfficientVCDStorage, BinarySignalValue
    _EFFICIENT_AVAILABLE = True
except ImportError:
    _EFFICIENT_AVAILABLE = False


class VCDTimeSnapshot(VCDObject):
    """Time snapshot."""

    def __init__(self, time: int):
        """Initialize."""
        super().__init__()
        self._time = time
        self._states = {}

    def record_state(self, var, state):
        """Record current state."""
        if state is None:
            self._states[var] = 0
            return
        # Handle 'x' and 'z' values by replacing with '0'
        clean_state = state.replace("x", "0").replace("X", "0")
        clean_state = clean_state.replace("z", "0").replace("Z", "0")
        try:
            self._states[var] = int(clean_state, 2)
        except ValueError:
            self._states[var] = 0

    @property
    def states(self):
        """Get states."""
        return self._states

    def pack(self):
        """Pack."""
        return {"time": self._time, "states": self._states}


class VCDCompiler(StreamingVCDParser, VCDHierarchyAnalysisMixin):
    """VCD compiler with efficient storage option."""

    def __init__(self, delta_evts: bool = True, use_efficient_format: bool = True, **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
        self._time_slice = None
        self._slice_count = 0
        self._delta = delta_evts
        self._dest = None
        self._modified_variables = []
        
        # Use efficient storage format if available
        self._use_efficient_format = use_efficient_format and _EFFICIENT_AVAILABLE
        if self._use_efficient_format:
            self._efficient_storage = EfficientVCDStorage()
            self._time_snapshots = {}  # time -> snapshot data
        
        # Track compilation statistics
        self._stats = {
            'variables_count': 0,
            'time_slices': 0,
            'total_changes': 0,
            'compression_ratio': 0.0
        }

    def _header(self):
        """Get header."""
        return {"vars": 0, "slices": 0}

    def parse(self, data, dest):
        """Parse."""
        self._dest = dest
        pickle.dump("DUMP_START", dest)
        super().parse(data)
        pickle.dump("DUMP_END", dest)

    def record_time_slice(self, time: int):
        """Record time slice."""
        self._time_slice = VCDTimeSnapshot(time)

    def initial_value_handler(self, stmt, fields):
        """Initial value handler with efficient storage."""
        var = self.variables[fields["var"]]
        
        if self._use_efficient_format:
            # Store in efficient format
            var_id = fields["var"]
            value = fields["value"]
            self._efficient_storage.set_value(var_id, 0, value)
            self._stats['total_changes'] += 1
        
        # Also maintain legacy format for compatibility
        if self._time_slice:
            self._time_slice.record_state(var, fields["value"])

    def value_change_handler(self, stmt, fields):
        """Value changes with efficient storage."""
        var = self.variables[fields["var"]]
        var.value = fields["value"]
        self._modified_variables.append(var.identifiers[0])
        
        if self._use_efficient_format:
            # Store in efficient format
            var_id = fields["var"]
            value = fields["value"]
            self._efficient_storage.set_value(var_id, self.current_time, value)
            self._stats['total_changes'] += 1

    def _state_change_handler(self, old_state, new_state):
        """Detect state transition with efficient metadata."""
        super()._state_change_handler(old_state, new_state)
        if old_state == "header":
            # header done, dump variables
            self._stats['variables_count'] = len(self.variables)
            
            if self._use_efficient_format:
                # Add variables to efficient storage 
                for var_id, var in self.variables.items():
                    # Variables were already added during header parsing via hierarchy mixin
                    pass
                
                # Dump efficient format metadata
                metadata = {
                    'format_version': 'efficient_v1',
                    'variables_count': len(self.variables),
                    'efficient_storage': True
                }
                pickle.dump(metadata, self._dest)
            
            # Legacy format
            for var in self.variables.values():
                pickle.dump(var.pack(), self._dest)
            pickle.dump("VARS_END", self._dest)

    def clock_change_handler(self, time):
        """Handle time."""
        if time == 0:
            return
        self.record_time_slice(time)
        if self._delta is False:
            for var in self.variables.values():
                # update variable:
                self._time_slice.record_state(var.identifiers[0], var.value)
        else:
            for varid in self._modified_variables:
                self._time_slice.record_state(
                    varid, self.variables[varid].value
                )

        # dump time slice
        pickle.dump(self._time_slice.pack(), self._dest)
        self._slice_count += 1
        self._stats['time_slices'] += 1
        self._modified_variables = []
    
    # Efficient storage query methods
    def get_compilation_statistics(self):
        """Get comprehensive compilation statistics."""
        if self._use_efficient_format:
            # Calculate compression ratio
            estimated_string_size = self._stats['total_changes'] * 32  # Rough estimate
            binary_size = len(self._efficient_storage.variables) * 16  # Rough estimate
            self._stats['compression_ratio'] = estimated_string_size / max(binary_size, 1)
        
        return self._stats.copy()
    
    def export_efficient_storage(self):
        """Export the efficient storage backend for external use."""
        if self._use_efficient_format:
            return self._efficient_storage
        return None
    
    def get_variable_history_efficient(self, var_id: str, start_time: int = None, end_time: int = None):
        """Get variable history using efficient time-indexed lookups."""
        if self._use_efficient_format and var_id in self._efficient_storage.variables:
            var = self._efficient_storage.variables[var_id]
            if start_time is not None and end_time is not None:
                return var.get_changes_in_range(start_time, end_time)
            else:
                return var.history.get_all_changes()
        return []
    
    def query_value_at_time_efficient(self, var_id: str, time: int):
        """Query variable value at specific time using efficient storage."""
        if self._use_efficient_format:
            binary_val = self._efficient_storage.get_value(var_id, time)
            return binary_val.to_string() if binary_val else None
        return None
