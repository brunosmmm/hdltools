"""VCD value trigger."""

import re
from uuid import uuid4
from typing import Optional, Union
from hdltools.vcd import VCDObject, VCDScope
from hdltools.patterns import Pattern


class VCDTriggerError(Exception):
    """Trigger error."""


class VCDTriggerDescriptor(VCDObject):
    """VCD Trigger descriptor."""

    DESCRIPTOR_REGEX = re.compile(
        r"([a-zA-Z_0-9:]+)\s*==\s*([Xx0-9A-Fa-f]+h?)"
    )

    def __init__(
        self,
        scope: Union[VCDScope, str],
        name: str,
        value: Union[Pattern, str],
        vcd_var: Optional[str] = None,
        negate: bool = False,
    ):
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
        self._vcd_var = vcd_var
        self._negate = negate

    @property
    def inverted(self):
        """Get if logic is inverted."""
        return self._negate

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

    @property
    def vcd_var(self):
        """VCD Variable name."""
        return self._vcd_var

    @vcd_var.setter
    def vcd_var(self, value):
        """Set vcd variable name."""
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        self._vcd_var = value

    def __repr__(self):
        """Get representation."""
        op = "==" if not self._negate else "!="
        return "{{{}::{}{}{}}}".format(
            str(self.scope), self.name, op, self.value
        )

    def match_var(
        self, scope: VCDScope, name: str, vcd_var: Optional[str] = None
    ) -> bool:
        """Match variable description."""
        if vcd_var is not None and self.vcd_var is not None:
            # prefer comparison using vcd variable name
            if vcd_var != self.vcd_var:
                return False
        else:
            if scope != self.scope:
                return False
            if name != self.name:
                return False

        return True

    def match_value(self, value: str) -> bool:
        """Match value."""
        if self._negate:
            return not self.value.match(value)

        return self.value.match(value)

    def match(
        self,
        scope: VCDScope,
        name: str,
        value: str,
        vcd_var: Optional[str] = None,
    ) -> bool:
        """Match against variable state."""
        if self.match_var(scope, name, vcd_var) is False:
            return False
        return self.match_value(value)

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
        return hash(tuple([self.scope, self.name, self.value]))


class VCDTriggerFSM:
    """Trigger FSM abstract class."""

    def __init__(self, **kwargs):
        """Initialize."""
        self._event_start_cb = None
        self._event_end_cb = None
        self._event_timeout_cb = None
        self._trigger_cb = None
        self._armed = False
        self._triggered = False
        self._evt_start_fired = False
        trigger_id = kwargs.get("trigger_id")
        if trigger_id is not None:
            self._trigger_id = trigger_id
        else:
            self._trigger_id = uuid4()

        evt_name = kwargs.get("evt_name")
        self._evt_name = evt_name
        self._current_evt_uuid = None
        self._last_evt_uuid = None
        self._event_ends_now = False

    @property
    def current_evt(self):
        """Get currently occurring event id."""
        return self._current_evt_uuid

    @property
    def last_evt(self):
        """Get last event id."""
        return self._last_evt_uuid

    @property
    def event_ending(self):
        """Get whether event ends now."""
        return self._event_ends_now

    @property
    def event_end_cb(self):
        """Get end callback."""
        return self._event_end_cb

    @event_end_cb.setter
    def event_end_cb(self, value):
        """Set event end callback."""
        if not callable(value):
            raise TypeError("value must be a callable")
        if self.trigger_armed:
            raise RuntimeError("cannot change event callback while armed")
        self._event_end_cb = value

    @property
    def event_start_cb(self):
        """Get start callback."""
        return self._event_start_cb

    @event_start_cb.setter
    def event_start_cb(self, value):
        """Set event start callback."""
        if not callable(value):
            raise TypeError("value must be a callable")
        if self.trigger_armed:
            raise RuntimeError("cannot change event callback while armed")
        self._event_start_cb = value

    @property
    def event_timeout_cb(self):
        """Get timeout callback."""
        return self._event_timeout_cb

    @event_timeout_cb.setter
    def event_timeout_cb(self, value):
        """Set event end callback."""
        if not callable(value):
            raise TypeError("value must be a callable")
        if self.trigger_armed:
            raise RuntimeError("cannot change event callback while armed")
        self._event_timeout_cb = value

    @property
    def has_timeout(self):
        """Get if this trigger has a timeout."""
        return self._event_timeout_cb is not None

    @property
    def evt_name(self):
        """Get event name."""
        return self._evt_name

    @property
    def triggerid(self):
        """Get trigger id."""
        return self._trigger_id

    @property
    def sensitivity_list(self):
        """Get current sensitivity list."""
        raise NotImplementedError

    @property
    def global_sensitivity_list(self):
        """Get global sensitivity list."""
        raise NotImplementedError

    def trigger_reset(self):
        """Reset configuration."""
        if self._armed:
            raise VCDTriggerError(
                "cannot modify trigger configuration while armed"
            )
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
        self._evt_start_fired = False
        self._event_ends_now = False
        self._triggered = False
        self._armed = True

    def disarm_trigger(self):
        """Disarm trigger."""
        if self._armed is False:
            raise VCDTriggerError("not armed")
        self._armed = False

    def _fire_trigger(self, disarm=True):
        """Fire trigger."""
        if disarm:
            self.disarm_trigger()
        self._triggered = True
        if self._current_evt_uuid is None:
            # had no start event call
            self._current_evt_uuid = uuid4()
        if self._event_end_cb is None:
            self._event_ends_now = True
        if self._trigger_cb is not None:
            self._trigger_cb(self)
        if self._event_end_cb is None:
            # ends here
            self._last_evt_uuid = self._current_evt_uuid
            self._current_evt_uuid = None

    def _event_starts(self):
        """Event starts."""
        if self._event_start_cb and not self._evt_start_fired:
            self._current_evt_uuid = uuid4()
            self._evt_start_fired = True
            self._event_start_cb(self)

    def _event_ends(self):
        """Event ends."""
        self.disarm_trigger()
        self._event_ends_now = True
        if self._event_end_cb:
            self._event_end_cb(self)
        self._last_evt_uuid = self._current_evt_uuid
        self._current_evt_uuid = None

    def _event_timeout(self):
        """Event timeout."""
        if self._event_timeout_cb:
            self._event_timeout_cb(self)

    def check_and_fire(self, time=None):
        """Check current state and fire."""
        raise NotImplementedError

    def advance(self, var, value, time=None):
        """Advance without variable check."""
        raise NotImplementedError

    def match_and_advance(self, var, value, time=None):
        """Update function."""
        raise NotImplementedError
