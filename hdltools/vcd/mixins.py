"""VCD Parser mixins."""

from collections import deque
from hdltools.vcd.parser import SCOPE_PARSER, UPSCOPE_PARSER, VAR_PARSER
from hdltools.vcd import VCDVariable, VCDScope


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


class VCDParserMixin:
    """VCD Parser mixin abstract class."""

    def __init__(self):
        """Initialize."""
        super().__init__()
        self._mixin_init()

    def _mixin_init(self):
        """Mixin initialization."""
        raise NotImplementedError


class VCDHierarchyAnalysisMixin(VCDParserMixin):
    """Hierarchical analysis mixin."""

    def __init__(self):
        """Initialize."""
        super().__init__()
        self._scope_stack = deque()
        self._scope_map = ScopeMap()
        self._vars = {}

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

    def _enter_scope(self, name):
        """Enter scope."""
        self._scope_map.add_hierarchy(self.current_scope, name)
        self._scope_stack.append(name)

    def _exit_scope(self):
        """Exit scope."""
        self._scope_stack.pop()

    def _mixin_init(self):
        """Mixin initialization."""
        self.add_state_hook("header", self._header_hook)

    def _header_hook(self, state, stmt, fields):
        """Header state hook."""
        if stmt == SCOPE_PARSER:
            # enter scope
            self._enter_scope(fields["sname"])
            return

        if stmt == UPSCOPE_PARSER:
            self._exit_scope()
            return

        if stmt == VAR_PARSER:
            cur_scope = VCDScope(*self.current_scope)
            var = VCDVariable.from_tokens(scope=cur_scope, **fields)
            self._vars[fields["id"]] = var

    @property
    def variables(self):
        """Get variables."""
        return self._vars
