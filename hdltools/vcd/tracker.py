"""VCD Value tracker."""

from collections import deque
from hdltools.vcd.parser import (
    BaseVCDParser,
    VCDParserError,
    SCOPE_PARSER,
    UPSCOPE_PARSER,
    VAR_PARSER,
)
from hdltools.vcd import VCDVariable
from hdltools.vcd.mixins import VCDHierarchyAnalysisMixin
from hdltools.patterns import Pattern


# TODO: multi value tracker
class VCDValueTracker(BaseVCDParser, VCDHierarchyAnalysisMixin):
    """VCD Value tracker.

    Track a tagged value through system hierarchy.
    """

    def __init__(self, track: Pattern):
        """Initialize."""
        super().__init__()
        if not isinstance(track, Pattern):
            raise TypeError("track must be a Pattern object")
        self._track_value = track
        self._track_history = []
        self._stmt_count = 0
        self._vars = {}

    def _parse_progress(self):
        """Track parsing progress."""
        self._stmt_count += 1
        # print("DEBUG: #lines = {}".format(self._current_line))

    def header_statement_handler(self, stmt, fields):
        """Handle header statements.

        Build variable-scope map.
        """
        self._parse_progress()

        if stmt == VAR_PARSER:
            var = VCDVariable.from_tokens(scope=self.current_scope, **fields)
            self._vars[fields["id"]] = var

    def initial_value_handler(self, stmt, fields):
        """Handle initial values."""
        self._parse_progress()
        if self._track_value.match(fields["value"]):
            # found
            var = self._vars[fields["var"]]
            self._add_to_history(var.scope, var.name)

    def value_change_handler(self, stmt, fields):
        """Handle value change."""
        self._parse_progress()
        if self._track_value.match(fields["value"]):
            if fields["var"] not in self._vars:
                raise VCDParserError(
                    'unknown variable in change event: "{}"'.format(
                        fields["var"]
                    )
                )
            var = self._vars[fields["var"]]
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

    def _add_to_history(self, scope, signal, time):
        """Add to history."""
        self._track_history.append((scope, signal, time))

    def parse(self, data):
        """Parse."""
        self._stmt_count = 0
        return super().parse(data)
