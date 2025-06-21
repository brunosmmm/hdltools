"""Hierarchical mixins."""

from collections import deque
from typing import Optional, Set
from hdltools.vcd.parser import SCOPE_PARSER, UPSCOPE_PARSER, VAR_PARSER
from hdltools.vcd.mixins import VCDParserMixin, ScopeMap
from hdltools.vcd import VCDScope
from hdltools.vcd.variable import VCDVariable


class VCDHierarchyAnalysisMixin(VCDParserMixin):
    """Hierarchical analysis mixin."""

    def __init__(self, debug=False, **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
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
            if fields["id"] in self._vars:
                # add alias
                self._vars[fields["id"]].add_alias(
                    cur_scope, name=fields["name"]
                )
            else:
                var = VCDVariable.from_tokens(scope=cur_scope, **fields)
                self._vars[fields["id"]] = var
            return

    @property
    def variables(self):
        """Get variables."""
        return self._vars

    def variable_search(
        self, var_name, scope: Optional[VCDScope] = None, aliases: bool = False
    ) -> Set[VCDVariable]:
        """Search for variable with efficient indexing when available."""
        
        # Try to use efficient storage if available
        if hasattr(self, '_use_efficient') and self._use_efficient:
            # Use efficient indexed search
            scope_str = str(scope) if scope is not None else None
            
            # Try efficient search first
            try:
                efficient_results = self.find_variables_efficient(
                    name=var_name, 
                    scope=scope_str
                )
                # Convert back to set of VCDVariable objects
                return set(efficient_results)
            except (AttributeError, KeyError):
                # Fall back to legacy search if efficient storage not available
                pass
        
        # Legacy linear search implementation
        candidates = set()
        for var in self._vars.values():
            if aliases:
                for alias_scope, alias_name in var.aliases:
                    if scope is not None:
                        if alias_scope != scope:
                            continue
                    if alias_name == var_name:
                        candidates |= {var}
                        break
            if scope is not None:
                if var.scope != scope:
                    continue
            if var.name == var_name:
                candidates |= {var}

        return candidates
