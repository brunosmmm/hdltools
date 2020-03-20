"""Hierarchical mixins."""

from collections import deque
from hdltools.vcd.parser import SCOPE_PARSER, UPSCOPE_PARSER, VAR_PARSER
from hdltools.vcd.mixins import VCDParserMixin, ScopeMap
from hdltools.vcd import VCDVariable, VCDScope


class VCDHierarchyAnalysisMixin(VCDParserMixin):
    """Hierarchical analysis mixin."""

    def __init__(self, debug=False, **kwargs):
        """Initialize."""
        super().__init__()
        self._scope_stack = deque()
        self._scope_map = ScopeMap()
        self._vars = {}
        self._debug = debug

        self.add_state_hook("header", self._header_hook)

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
