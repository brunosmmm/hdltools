"""VCD Value tracker."""

import re
from typing import Tuple, Optional, Union
from hdltools.vcd import VCDScope
from hdltools.vcd.parser import BaseVCDParser, VCDParserError
from hdltools.vcd.mixins import VCDTriggerMixin
from hdltools.patterns import Pattern
from hdltools.vcd.trigger import VCDTriggerDescriptor
from hdltools.vcd.history import VCDValueHistory, VCDValueHistoryEntry


# TODO: multi value tracker
# FIXME: avoid expensive duplications of data
class VCDValueTracker(BaseVCDParser, VCDTriggerMixin):
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
        preconditions: Optional[Tuple[VCDTriggerDescriptor]] = None,
        postconditions: Optional[Tuple[VCDTriggerDescriptor]] = None,
        time_range: Optional[Tuple[int, int]] = None,
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
        self._wait_precondition = False
        self._wait_postcondition = False
        self._postconditions = []

        if time_range is not None:
            if not isinstance(time_range, (tuple, list)):
                raise TypeError("time_range must be a list")
            if len(time_range) != 2:
                raise ValueError("time_range must have 2 elements exactly")
            start, end = time_range
            if not isinstance(start, int) or not isinstance(end, int):
                raise TypeError("start and end in time_range must be integers")
            self._hist_start = start
            self._hist_end = end
        else:
            self._hist_start = None
            self._hist_end = None

        if postconditions is not None:
            if isinstance(postconditions, VCDTriggerDescriptor):
                self._postconditions.append(postconditions)
            else:
                for postcondition in postconditions:
                    if not isinstance(postcondition, VCDTriggerDescriptor):
                        raise TypeError(
                            "precondition must be a VCDTriggerDescriptor object"
                        )
                    self._postconditions.append(postcondition)
        if preconditions is not None:
            self._wait_precondition = True
            if isinstance(preconditions, VCDTriggerDescriptor):
                self.add_trigger_level(preconditions)
            else:
                for precondition in preconditions:
                    if not isinstance(precondition, VCDTriggerDescriptor):
                        raise TypeError(
                            "precondition must be a VCDTriggerDescriptor object"
                        )
                    self.add_trigger_level(precondition)

            # arm trigger
            self.trigger_callback = self._precondition_callback
            self.arm_trigger()

    # FIXME: this is a placeholder
    def _precondition_callback(self):
        """Precondition callback."""
        if self._debug:
            print(
                "DEBUG: {} trigger reached_preconditions".format(
                    self.current_time
                )
            )
        self._wait_precondition = False
        # setup postconditions
        if self._postconditions:
            self._wait_postcondition = True
            self.trigger_reset()
            for postcondition in self._postconditions:
                self.add_trigger_level(postcondition)

            self.trigger_callback = self._postcondition_callback
            self.arm_trigger()

    def _postcondition_callback(self):
        """Postcondition callback."""
        if self._debug:
            print(
                "DEBUG: {} trigger reached_postconditions".format(
                    self.current_time
                )
            )
        self._wait_postcondition = False
        self._abort_parser()

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
        if (
            self._hist_start is not None
            and self.current_time < self._hist_start
        ):
            return
        if self._hist_end is not None and self.current_time > self._hist_end:
            # done
            self._abort_parser()
        if self._wait_precondition and self._triggered is False:
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
