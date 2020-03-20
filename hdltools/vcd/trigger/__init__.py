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


class VCDTriggerEvent(VCDObject):
    """VCD trigger event."""

    EVENT_TYPES = ("condition", "trigger")

    def __init__(
        self,
        evt_type: str,
        time: int,
        evt: Optional[VCDTriggerDescriptor] = None,
    ):
        """Initialize."""
        if not isinstance(time, int):
            raise TypeError("time must be an integer")
        self._time = time
        if evt_type not in self.EVENT_TYPES:
            raise ValueError("invalid event type")
        self._type = evt_type

        if evt is None:
            self._evt = None
        elif not isinstance(evt, VCDTriggerDescriptor):
            raise TypeError("evt must be a VCDTriggerDescriptor object")
        else:
            self._evt = evt

    @property
    def time(self):
        """Get occurrence time."""
        return self._time

    @property
    def evt_type(self):
        """Get event type."""
        return self._type

    @property
    def evt(self):
        """Get trigger descriptor."""
        return self._evt
