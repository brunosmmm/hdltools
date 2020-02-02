"""VCD Value tracker."""

from collections import deque
from hdltools.vcd.parser import (
    BaseVCDParser,
    SCOPE_PARSER,
    UPSCOPE_PARSER,
    VAR_PARSER,
)
from hdltools.vcd import VCDVariable
from hdltools.patterns import Pattern


# TODO: multi value tracker
class VCDValueTracker(BaseVCDParser):
    """VCD Value tracker.

    Track a tagged value through system hierarchy.
    """

    def __init__(self, track: Pattern):
        """Initialize."""
        if not isinstance(track, Pattern):
            raise TypeError("track must be a Pattern object")
        self._track_value = track
        self._track_history = []
        self._scope_stack = deque()
        self._vars = {}

    def header_statement_handler(self, stmt, fields):
        """Handle header statements.

        Build variable-scope map.
        """
        if stmt == SCOPE_PARSER:
            # enter scope
            self._scope_stack.append(fields["sname"])
            return

        if stmt == UPSCOPE_PARSER:
            self._scope_stack.popleft()
            return

        if stmt == VAR_PARSER:
            var = VCDVariable.from_tokens(scope=self.curent_scope, **fields)
            self._vars[fields["id"]] = var

    def initial_value_handler(self, stmt, fields):
        """Handle initial values."""
        if self._track_value.match(fields["value"]):
            # found
            var = self._vars[fields["var"]]
            self._add_to_history(var.scope, var.name)

    def value_change_handler(self, stmt, fields):
        """Handle value change."""
        if self._track_value.match(fields["value"]):
            var = self._vars[fields["var"]]
            self._add_to_history(var.scope, var.name)

    @property
    def current_scope_depth(self):
        """Get current sope depth."""
        return len(self._scope_stack)

    @property
    def current_scope(self):
        """Get current scope."""
        return tuple(self._scope_stack)

    def _add_to_history(self, scope, signal):
        """Add to history."""
        self._track_history.append((scope, signal))
