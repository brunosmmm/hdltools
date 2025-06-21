"""VCD to compact representation compiler."""

# import struct
import pickle
from hdltools.vcd import VCDObject
from hdltools.vcd.streaming_parser import StreamingVCDParser
from hdltools.vcd.mixins.hierarchy import VCDHierarchyAnalysisMixin


# class PackSnapshot(PackableType):
#     """Pack snapshot type."""

#     _pack_identifier = "0"

#     @classmethod
#     def pack(cls, what):
#         """Pack."""
#         buffer = bytearray()
#         struct.pack_into("c", buffer, 0, cls._pack_identifier)
#         buffer += pack(what.states)

#         return buffer


class VCDTimeSnapshot(VCDObject):
    """Time snapshot."""

    # _pack_type = PackSnapshot

    def __init__(self, time: int):
        """Initialize."""
        super().__init__()
        self._time = time
        self._states = {}

    def record_state(self, var, state):
        """Record current state."""
        self._states[var] = int(state, 2)

    @property
    def states(self):
        """Get states."""
        return self._states

    def _item_size(self):
        """Calcualte item size."""

    def pack(self):
        """Pack."""
        return {"time": self._time, "states": self._states}


# FIXME: this breaks with variables that are not initialized properly
class VCDCompiler(StreamingVCDParser, VCDHierarchyAnalysisMixin):
    """VCD compiler."""

    def __init__(self, delta_evts: bool = True, **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
        self._time_slice = None
        self._slice_count = 0
        self._delta = delta_evts
        self._dest = None
        self._modified_variables = []

    def _header(self):
        """Get header."""
        return {"vars": 0, "slices": 0}

    def parse(self, data, dest):
        """Parse."""
        print("DEBUG: starting")
        self._dest = dest
        pickle.dump("DUMP_START", dest)
        super().parse(data)
        pickle.dump("DUMP_END", dest)

    def record_time_slice(self, time: int):
        """Record time slice."""
        self._time_slice = VCDTimeSnapshot(time)

    def initial_value_handler(self, stmt, fields):
        """Initial value handler."""
        var = self.variables[fields["var"]]
        self._time_slice.record_state(var, fields["value"])

    def value_change_handler(self, stmt, fields):
        """Value changes."""
        var = self.variables[fields["var"]]
        var.value = fields["value"]
        self._modified_variables.append(var.identifiers[0])

    def _state_change_handler(self, old_state, new_state):
        """Detect state transition."""
        super()._state_change_handler(old_state, new_state)
        if old_state == "header":
            # header done, dump variables
            for var in self.variables.values():
                pickle.dump(var.pack(), self._dest)
            pickle.dump("VARS_END", self._dest)

    def clock_change_handler(self, time):
        """Handle time."""
        if time == 0:
            return
        if time % 100 == 0:
            print(f"DEBUG: @{time}", end="\r")
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
        self._modified_variables = []
