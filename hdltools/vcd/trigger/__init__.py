"""VCD value trigger."""

import re
from typing import Optional
from hdltools.vcd import VCDObject, VCDScope
from hdltools.patterns import Pattern


class VCDTriggerError(Exception):
    """Trigger error."""


class VCDTriggerDescriptor(VCDObject):
    """VCD Trigger descriptor."""

    DESCRIPTOR_REGEX = re.compile(
        r"([a-zA-Z_0-9:]+)\s*==\s*([Xx0-9A-Fa-f]+h?)"
    )

    def __init__(self, scope, name, value):
        """Initialize."""
        super().__init__()
        if isinstance(scope, VCDScope):
            self._scope = scope
        elif isinstance(scope, str):
            self._scope, _ = VCDScope.from_str(scope)
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
        scope = "::".join(fragments[:-1])
        return VCDTriggerDescriptor(scope, name, m.group(2))

    def __repr__(self):
        """Get representation."""
        return "{{{}::{}=={}}}".format(str(self.scope), self.name, self.value)

    def match(self, scope, name, value):
        """Match against variable state."""
        if scope != self.scope:
            return False
        if name != self.name:
            return False
        return self.value.match(value)

    def __eq__(self, other):
        """Check if is equivalent."""
        if not isinstance(other, VCDTriggerDescriptor):
            return False

        if self.value != other.value:
            return False
        if self.name != other.name:
            return False
        if self.scope != other.scope:
            return False

        return True

    def __hash__(self):
        """Get hash."""
        return hash(tuple(self.scope, self.name, self.value))
