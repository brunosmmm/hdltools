"""VCD Parser mixins."""

import re
from collections import deque
from hdltools.vcd.parser import SCOPE_PARSER, UPSCOPE_PARSER, VAR_PARSER
from hdltools.vcd import VCDVariable, VCDScope, VCDObject
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


class VCDTriggerError(Exception):
    """Trigger error."""


class VCDTriggerDescriptor(VCDObject):
    """VCD Trigger descriptor."""

    DESCRIPTOR_REGEX = re.compile(r"([a-zA-Z_0-9:]+)\s*==\s*([Xx0-9A-Fa-f])h?")

    def __init__(self, scope, name, value):
        """Initialize."""
        super().__init__()
        if isinstance(scope, VCDScope):
            self._scope = scope
        elif isinstance(scope, str):
            self._scope = VCDScope.from_str(scope)
        else:
            raise TypeError("scope must be either string or VCDScope object")
        self._name = name
        if isinstance(value, Pattern):
            self._value = value
        elif isinstance(value, (str, bytes)):
            self._value = Pattern(value)
        else:
            raise TypeError("value must be Pattern object or str or bytes")

    @property
    def scope(self):
        """Get scope."""
        return self._scope

    @property
    def name(self):
        """Get name."""
        return self._name

    @property
    def value(self):
        """Get value."""
        return self._value

    @staticmethod
    def from_str(descr):
        """Build from string."""
        # string will look like this:
        # scope::scope::scope::variable==PATTERN
        m = VCDTriggerDescriptor.DESCRIPTOR_REGEX.match(descr)
        if m is None:
            raise VCDTriggerError("invalid descriptor")
        fragments = m.group(1).split("::")
        name = fragments[-1]
        scope = "::".join(fragments[:-2])
        return VCDTriggerDescriptor(scope, name, m.group(2))


class VCDTriggerMixin(VCDHierarchyAnalysisMixin):
    """Trigger mixin."""

    def __init__(self):
        """Initialize."""
        super().__init__()
        self._levels = []
        self._current_level = 0
        self._trigger_cb = None
        self._armed = False
        self._triggered = False

        self.add_state_hook("dump", self._dump_hook)

    def add_trigger_level(self, trig):
        """Add a trigger level."""
        if self._armed:
            raise VCDTriggerError("cannot modify trigger levels while armed")
        if not isinstance(trig, VCDTriggerDescriptor):
            raise TypeError(
                "trigger level must be VCDTriggerDescriptor object"
            )
        self.levels.append(trig)

    def remove_trigger_level(self, trig_level):
        """Remove a trigger level."""
        if self._armed:
            raise VCDTriggerError("cannot modify trigger levels while armed")
        del self.levels[trig_level]

    def trigger_reset(self):
        """Reset trigger configurations."""
        if self._armed:
            raise VCDTriggerError(
                "cannot modify trigger configuration while armed"
            )
        self._levels = []
        self._current_level = 0
        self._trigger_cb = None
        self._armed = False
        self._triggered = False

    @property
    def trigger_callback(self):
        """Get trigger callback."""
        return self._trigger_cb

    @trigger_callback.setter
    def trigger_callback(self, cb):
        """Set trigger callback."""
        if self._armed:
            raise VCDTriggerError("cannot change callback while armed")
        if not callable(cb):
            raise TypeError("trigger callback must be a callable")
        self._trigger_cb = cb

    @property
    def current_trigger_level(self):
        """Get current trigger level."""
        return self._current_level

    @property
    def current_trigger(self):
        """Get current trigger level description."""
        return self._levels[self._current_level]

    @property
    def trigger_levels(self):
        """Get trigger level count."""
        return len(self._levels)

    @property
    def trigger_armed(self):
        """Get whether trigger is armed."""
        return self._armed

    @property
    def triggered(self):
        """Get whether triggered."""
        return self._triggered

    def arm_trigger(self):
        """Arm trigger."""
        if self._armed:
            raise VCDTriggerError("already armed")
        self._triggered = False
        self._current_level = 0
        self._armed = True

    def disarm_trigger(self):
        """Disarm trigger."""
        if self._armed is False:
            raise VCDTriggerError("not armed")
        self._armed = False

    def _mixin_init(self):
        """Mixin initialization."""

    def _dump_hook(self, state, stmt, fields):
        """Value change hook."""
        if self._armed is False:
            return

        # match
        trig = self.current_trigger
        var = self._vars[fields["vars"]]
        if (
            var.scope == trig.scope
            and var.name == trig.name
            and trig.value.match(fields["value"])
        ):
            # is a match
            print(
                "DEBUG: reached trigger level {}".format(
                    self._current_level + 1
                )
            )
            self._current_level += 1

        if self._current_level == self.trigger_levels:
            self.disarm_trigger()
            self._triggered = True
            if self._trigger_cb is not None:
                self._trigger_cb()
