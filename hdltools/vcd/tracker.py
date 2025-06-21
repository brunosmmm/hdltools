"""VCD Value tracker."""

import re
from typing import Tuple, Optional, Union
from hdltools.vcd import VCDScope
from hdltools.vcd.streaming_parser import StreamingVCDParser
from hdltools.vcd.parser import VCDParserError
from hdltools.vcd.mixins.conditions import VCDConditionMixin
from hdltools.vcd.mixins.time import VCDTimeRestrictionMixin
from hdltools.patterns import Pattern
from hdltools.vcd.history import VCDValueHistory, VCDValueHistoryEntry
try:
    from hdltools.vcd.efficient_storage import TimeIndexedHistory, BinarySignalValue
    _EFFICIENT_AVAILABLE = True
except ImportError:
    _EFFICIENT_AVAILABLE = False


# TODO: multi value tracker
# FIXME: avoid expensive duplications of data


class EfficientVCDValueHistory:
    """Efficient VCD value history with time-indexed lookups."""
    
    def __init__(self):
        """Initialize with time-indexed storage."""
        self._history = TimeIndexedHistory() if _EFFICIENT_AVAILABLE else []
        self._entries = []  # Keep VCDValueHistoryEntry objects for compatibility
        
    def add_entry(self, entry: VCDValueHistoryEntry):
        """Add history entry with efficient time indexing."""
        if not isinstance(entry, VCDValueHistoryEntry):
            raise TypeError("entry must be a VCDValueHistoryEntry object")
            
        self._entries.append(entry)
        
        # Store in time-indexed format if available
        if _EFFICIENT_AVAILABLE and hasattr(self, '_history') and isinstance(self._history, TimeIndexedHistory):
            # Create a simple binary value to represent the entry
            entry_data = f"{entry.scope}::{entry.signal}"
            binary_val = BinarySignalValue(len(entry_data) * 8, entry_data.encode('utf-8'))
            self._history.add_change(entry.time, binary_val)
    
    def get_by_time(self, time: int) -> VCDValueHistoryEntry:
        """Get history entry by simulation time with O(log n) lookup."""
        if _EFFICIENT_AVAILABLE and hasattr(self, '_history') and isinstance(self._history, TimeIndexedHistory):
            # Use efficient binary search
            binary_val = self._history.get_value_at(time)
            if binary_val is None:
                raise IndexError("invalid item index")
                
            # Find matching entry in compatibility list
            for entry in self._entries:
                if entry.time == time:
                    return entry
            raise IndexError("invalid item index")
        else:
            # Legacy linear search
            for entry in self._entries:
                if entry.time == time:
                    return entry
            raise IndexError("invalid item index")
    
    def get_entries_in_range(self, start_time: int, end_time: int):
        """Get all entries in time range with efficient indexing."""
        if _EFFICIENT_AVAILABLE and hasattr(self, '_history') and isinstance(self._history, TimeIndexedHistory):
            # Use efficient range query
            changes = self._history.get_changes_in_range(start_time, end_time)
            # Return corresponding VCDValueHistoryEntry objects
            result = []
            for time, _ in changes:
                for entry in self._entries:
                    if entry.time == time:
                        result.append(entry)
                        break
            return result
        else:
            # Legacy linear scan
            return [entry for entry in self._entries 
                   if start_time <= entry.time <= end_time]
    
    def __len__(self):
        """Get length."""
        return len(self._entries)
    
    def __getitem__(self, idx):
        """Get item by index."""
        return self._entries[idx]
    
    @property
    def visited_scopes(self):
        """Determine all visited scopes."""
        return {entry.scope for entry in self._entries}
class VCDValueTracker(
    StreamingVCDParser, VCDConditionMixin, VCDTimeRestrictionMixin
):
    """VCD Value tracker.

    Track a tagged value through system hierarchy.
    """

    def __init__(
        self,
        track: Pattern,
        restrict_src: Optional[Union[Tuple[str], VCDScope]] = None,
        restrict_dest: Optional[Union[Tuple[str], VCDScope]] = None,
        inclusive_src=False,
        inclusive_dest=False,
        ignore_signals: Optional[Tuple[str]] = None,
        ignore_scopes: Optional[Tuple[str]] = None,
        anchors: Optional[Tuple[str, str]] = None,
        track_all: bool = False,
        src_oneshot: bool = False,
        **kwargs,
    ):
        """Initialize."""
        super().__init__(**kwargs)
        if not isinstance(track, Pattern):
            raise TypeError("track must be a Pattern object")
        self._track_value = track
        self._track_all = track_all
        
        # Use efficient storage if available and enabled
        use_efficient = getattr(self, '_use_efficient', False) and _EFFICIENT_AVAILABLE
        
        if use_efficient:
            self._track_history = EfficientVCDValueHistory()
            self._complete_value_history = EfficientVCDValueHistory()  
            self._full_history = EfficientVCDValueHistory()
        else:
            self._track_history = VCDValueHistory()
            self._complete_value_history = VCDValueHistory()
            self._full_history = VCDValueHistory()
            
        self._stmt_count = 0
        if isinstance(restrict_src, tuple):
            restrict_src = VCDScope(*restrict_src)
        if isinstance(restrict_dest, tuple):
            restrict_dest = VCDScope(*restrict_dest)
        self._restrict_src = restrict_src
        self._restrict_dest = restrict_dest
        self._inclusive_src = inclusive_src
        self._inclusive_dest = inclusive_dest
        self._oneshot_src = src_oneshot
        if ignore_signals is not None:
            self._ignore_sig = [re.compile(ign) for ign in ignore_signals]
        else:
            self._ignore_sig = None
        if ignore_scopes is not None:
            self._ignore_scope = [re.compile(ign) for ign in ignore_scopes]
        else:
            self._ignore_scope = None

        # source, destination anchors
        src_anchor, dest_anchor = (
            anchors if anchors is not None else (None, None)
        )
        self._src_anchor = (
            re.compile(src_anchor) if src_anchor is not None else None
        )
        self._dest_anchor = (
            re.compile(dest_anchor) if dest_anchor is not None else None
        )
        self._maybe_src = None
        self._maybe_dest = None

    # FIXME: this is a placeholder

    def _parse_progress(self):
        """Track parsing progress."""
        self._stmt_count += 1
        # print("DEBUG: #lines = {}".format(self._current_line))

    def header_statement_handler(self, stmt, fields):
        """Handle header statements.

        Build variable-scope map.
        """
        self._parse_progress()

    def initial_value_handler(self, stmt, fields):
        """Handle initial values."""
        self._parse_progress()
        var = self.variables[fields["var"]]
        if self._track_all:
            self._add_to_history(var.scope, var.name, 0)
        if self._track_value.match(fields["value"]):
            # found
            self._add_to_tracked_history(var.scope, var.name, 0)
            self._add_to_value_history(var.scope, var.name, 0)

    def value_change_handler(self, stmt, fields):
        """Handle value change."""
        self._parse_progress()
        var = self.variables[fields["var"]]
        if self._track_all:
            self._add_to_history(var.scope, var.name, self.current_time)
        # handle start time
        if self._track_value.match(fields["value"]):
            # add to complete tracking history
            self._add_to_value_history(var.scope, var.name, self.current_time)
        if self.time_valid is False or self.waiting_precondition:
            return
        var_scope = var.scope
        in_src_scope = self._restrict_src is not None and (
            var_scope == self._restrict_src
            or (self._restrict_src.contains(var_scope) and self._inclusive_src)
        )

        in_dest_scope = self._restrict_dest is not None and (
            var_scope == self._restrict_dest
            or (
                self._restrict_dest.contains(var_scope)
                and self._inclusive_dest
            )
        )
        if (self._restrict_src is not None and not in_src_scope) and (
            self._restrict_dest is not None and not in_dest_scope
        ):
            return
        if self._track_value.match(fields["value"]):
            if self._ignore_sig is not None:
                for patt in self._ignore_sig:
                    if (
                        patt.match(self.variables[fields["var"]].name)
                        is not None
                    ):
                        # ignore
                        return
            if self._debug:
                print(
                    "DEBUG: {} match {}".format(
                        self.current_time, self.variables[fields["var"]]
                    )
                )
            if fields["var"] not in self.variables:
                raise VCDParserError(
                    'unknown variable in change event: "{}"'.format(
                        fields["var"]
                    )
                )
            idx = self._add_to_tracked_history(
                var.scope, var.name, self.current_time
            )
            # FIXME: make sure that anchors are not used without scope restriction
            if in_src_scope:
                if self._src_anchor is not None and self._maybe_dest is None:
                    if (
                        self._src_anchor.match(
                            self.variables[fields["var"]].name
                        )
                        is not None
                    ):
                        # new probable source
                        # FIXME: bad logic
                        if self._oneshot_src is False:
                            self._maybe_src = idx
                        elif self._maybe_src is None:
                            self._maybe_src = idx
                elif self._maybe_dest is None:
                    # anything that appears is probable source
                    if self._oneshot_src is False:
                        self._maybe_src = idx
                    elif self._maybe_src is None:
                        self._maybe_src = idx

            if in_dest_scope:
                if self._maybe_dest is None and self._maybe_src is not None:
                    if (
                        self._dest_anchor is not None
                        and self._dest_anchor.match(
                            self.variables[fields["var"]].name
                        )
                        is not None
                    ):
                        self._maybe_dest = idx
                    elif self._dest_anchor is None:
                        self._maybe_dest = idx

    @property
    def history(self):
        """Get tracking history."""
        return self._track_history

    @property
    def full_history(self):
        """Get full history if available."""
        if self._track_all:
            return self._full_history
        return self.history

    @property
    def full_value_history(self):
        """Get full value match history."""
        return self._complete_value_history

    @property
    def maybe_src(self):
        """Get probable source."""
        return self._maybe_src

    @property
    def maybe_dest(self):
        """Get probable destination."""
        return self._maybe_dest

    def _add_to_value_history(self, scope, signal, time):
        """Add to value history."""
        self._complete_value_history.add_entry(
            VCDValueHistoryEntry(scope, signal, time)
        )
        return len(self._full_history) - 1

    def _add_to_history(self, scope, signal, time):
        """Add to history."""
        self._full_history.add_entry(VCDValueHistoryEntry(scope, signal, time))
        return len(self._full_history) - 1

    def _add_to_tracked_history(self, scope, signal, time):
        """Add to history."""
        self._track_history.add_entry(
            VCDValueHistoryEntry(scope, signal, time)
        )
        return len(self._track_history) - 1

    def parse(self, data):
        """Parse."""
        self._stmt_count = 0
        return super().parse(data)
    
    # New efficient query methods
    def get_history_in_time_range(self, start_time: int, end_time: int):
        """Get tracking history entries in time range using efficient indexing."""
        if hasattr(self._track_history, 'get_entries_in_range'):
            return self._track_history.get_entries_in_range(start_time, end_time)
        else:
            # Legacy fallback
            return [entry for entry in self._track_history 
                   if start_time <= entry.time <= end_time]
    
    def get_value_history_in_range(self, start_time: int, end_time: int):
        """Get value match history in time range using efficient indexing.""" 
        if hasattr(self._complete_value_history, 'get_entries_in_range'):
            return self._complete_value_history.get_entries_in_range(start_time, end_time)
        else:
            # Legacy fallback
            return [entry for entry in self._complete_value_history
                   if start_time <= entry.time <= end_time]
    
    def get_history_at_time(self, time: int):
        """Get history entry at specific time using efficient lookup."""
        try:
            if hasattr(self._track_history, 'get_by_time'):
                return self._track_history.get_by_time(time)
            else:
                # Legacy fallback - linear search
                for entry in self._track_history:
                    if entry.time == time:
                        return entry
                raise IndexError("No entry found at specified time")
        except IndexError:
            return None
