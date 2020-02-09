"""VCD Value tracker."""

from typing import Tuple, Optional, Union
from hdltools.vcd import VCDScope
from hdltools.vcd.parser import BaseVCDParser, VCDParserError
from hdltools.vcd.mixins import VCDHierarchyAnalysisMixin
from hdltools.patterns import Pattern


# TODO: multi value tracker
class VCDValueTracker(BaseVCDParser, VCDHierarchyAnalysisMixin):
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
    ):
        """Initialize."""
        super().__init__()
        if not isinstance(track, Pattern):
            raise TypeError("track must be a Pattern object")
        self._track_value = track
        self._track_history = []
        self._stmt_count = 0
        if isinstance(restrict_src, tuple):
            restrict_src = VCDScope(*restrict_src)
        if isinstance(restrict_dest, tuple):
            restrict_dest = VCDScope(*restrict_dest)
        self._restrict_src = restrict_src
        self._restrict_dest = restrict_dest
        self._inclusive_src = inclusive_src
        self._inclusive_dest = inclusive_dest

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
        if self._track_value.match(fields["value"]):
            # found
            var = self.variables[fields["var"]]
            self._add_to_history(var.scope, var.name)

    def value_change_handler(self, stmt, fields):
        """Handle value change."""
        self._parse_progress()
        var_scope = self.variables[fields["var"]].scope
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
            print("DEBUG: current time = {}".format(self.current_time))
            print(
                "DEBUG: found value match, variable is {}".format(
                    self.variables[fields["var"]]
                )
            )
            if fields["var"] not in self.variables:
                raise VCDParserError(
                    'unknown variable in change event: "{}"'.format(
                        fields["var"]
                    )
                )
            var = self.variables[fields["var"]]
            self._add_to_history(var.scope, var.name, self.current_time)

    @property
    def current_scope_depth(self):
        """Get current sope depth."""
        return len(self._scope_stack)

    @property
    def current_scope(self):
        """Get current scope."""
        return tuple(self._scope_stack)

    @property
    def scope_hier(self):
        """Get scope hierarchy."""
        return self._scope_map

    @property
    def history(self):
        """Get tracking history."""
        return tuple(self._track_history)

    def _add_to_history(self, scope, signal, time):
        """Add to history."""
        self._track_history.append((scope, signal, time))

    def parse(self, data):
        """Parse."""
        self._stmt_count = 0
        return super().parse(data)
