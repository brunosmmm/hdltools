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


class ScopeMap:
    """Scope map."""

    def __init__(self):
        """Initialize."""
        self._map = {}

    def __getitem__(self, index):
        """Get item."""
        if not isinstance(index, tuple):
            raise TypeError("index must be a tuple")

        current_map = self._map
        for element in index:
            current_map = current_map[element]

        return current_map

    def add_hierarchy(self, index, hier_name):
        """Add hierarchy."""
        outer = self[index]
        if hier_name in outer:
            raise ValueError("scope already exists.")
        outer[hier_name] = {}

    def dump(self):
        """Print out."""
        ScopeMap._dump(self._map)

    @staticmethod
    def _dump(hier, indent=0):
        """Print out."""

        current_indent = "  " * indent
        for name, _hier in hier.items():
            print(current_indent + name)
            ScopeMap._dump(_hier, indent + 1)


# TODO: multi value tracker
class VCDValueTracker(BaseVCDParser):
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
        self._scope_stack = deque()
        self._scope_map = ScopeMap()
        self._vars = {}

    def _enter_scope(self, name):
        """Enter scope."""
        self._scope_map.add_hierarchy(self.current_scope, name)
        self._scope_stack.append(name)

    def _exit_scope(self):
        """Exit scope."""
        self._scope_stack.pop()

    def header_statement_handler(self, stmt, fields):
        """Handle header statements.

        Build variable-scope map.
        """
        if stmt == SCOPE_PARSER:
            # enter scope
            self._enter_scope(fields["sname"])
            return

        if stmt == UPSCOPE_PARSER:
            self._exit_scope()
            return

        if stmt == VAR_PARSER:
            var = VCDVariable.from_tokens(scope=self.current_scope, **fields)
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
