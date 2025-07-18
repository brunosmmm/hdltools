"""Trigger state machines."""

from typing import Optional, Tuple
from hdltools.vcd.trigger import (
    VCDTriggerDescriptor,
    VCDTriggerError,
    VCDTriggerFSM,
)
from hdltools.vcd.trigger.event import VCDTriggerEvent


class BranchingTrigger(VCDTriggerFSM):
    """Branching trigger state machine."""

    def __init__(self, **kwargs):
        """Initialize."""


class SimpleTrigger(VCDTriggerFSM):
    """Legacy trigger state machine."""

    def __init__(
        self,
        levels: Optional[Tuple[Tuple[VCDTriggerDescriptor]]] = None,
        debug=False,
        **kwargs
    ):
        """Initialize."""
        super().__init__(**kwargs)
        self._levels = []
        self._current_level = 0
        self._trigger_history = []
        self._debug = debug
        self._last_change = 0
        self._state_timeout = None

        if levels is not None:
            for level in levels:
                self.add_trigger_level(level)

    def add_trigger_level(self, *conds: VCDTriggerDescriptor):
        """Add a trigger level.

        Arguments
        ==========
          conds: Possible conditions, any (all or'ed together)
        """
        if self._armed:
            raise VCDTriggerError("cannot modify trigger levels while armed")
        for cond in conds:
            if not isinstance(cond, VCDTriggerDescriptor):
                raise TypeError(
                    "trigger level must be VCDTriggerDescriptor object"
                )
        self._levels.append(conds)

    def remove_trigger_level(self, trig_level):
        """Remove a trigger level."""
        if self._armed:
            raise VCDTriggerError("cannot modify trigger levels while armed")
        del self._levels[trig_level]

    def trigger_reset(self):
        """Reset trigger configurations."""
        super().trigger_reset()
        self._levels = []
        self._current_level = 0

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
    def trigger_history(self):
        """Get trigger event history."""
        return self._trigger_history

    @VCDTriggerFSM.sensitivity_list.getter
    def sensitivity_list(self):
        """Get current sensitivity list."""
        return self._levels[self._current_level]

    @VCDTriggerFSM.global_sensitivity_list.getter
    def global_sensitivity_list(self):
        """Get global sensitivity list."""
        conds = set()
        for level in self._levels:
            for cond in level:
                conds |= {cond}
        return list(conds)

    @VCDTriggerFSM.event_end_cb.setter
    def event_end_cb(self, value):
        """Ignore end callback setter."""
        self._event_end_cb = None

    @property
    def last_change(self):
        """Time of last change."""
        return self._last_change

    @property
    def state_timeout(self):
        """Timeout."""
        return self._state_timeout

    @state_timeout.setter
    def state_timeout(self, value):
        """Set timeout."""
        if not isinstance(value, int) and value is not None:
            raise TypeError("value must be int or None")
        if self.trigger_armed:
            raise RuntimeError("cannot change timeout while armed")
        self._state_timeout = value

    def arm_trigger(self):
        """Arm trigger."""
        super().arm_trigger()
        self._current_level = 0

    def _check_timeout(self, time):
        """Check if timeout occurred."""
        if (
            self.state_timeout is not None
            and time - self.last_change > self.state_timeout
            and self._current_level > 0
        ):
            # timeout! reset state
            self._last_change = time
            self._current_level = 0
            self._evt_start_fired = False
            self._event_timeout()
            return True
        return False

    def advance(self, cond, value, time):
        """Advance state."""
        if self.trigger_armed is False:
            return (False, None, False)
        if self._check_timeout(time):
            return (True, False, True)
        # Strip 'b' prefix from VCD binary values
        clean_value = value.lstrip('b') if isinstance(value, str) and value.startswith('b') else value
        if cond.match_value(clean_value):
            self._current_level += 1
            self._last_change = time
            return (True, True, True)
        else:
            return (False, False, False)

    def check_and_fire(self, time):
        """Check current state and fire."""
        if self._check_timeout(time):
            return
        if self._current_level > 0:
            self._event_starts()
        if self._current_level == self.trigger_levels:
            self._fire_trigger()

    def match_and_advance(self, var, value, time=None):
        """Value change hook."""
        if self.trigger_armed is False:
            return

        conds = self.current_trigger
        for cond in conds:
            if (
                var.scope == cond.scope
                and var.name == cond.name
                and cond.value.match(value)
            ):
                # is a match
                if self._debug:
                    print(
                        "DEBUG: {} trigger reach_level {} {}".format(
                            self.current_time,
                            self._current_level + 1,
                            self._levels[self._current_level],
                        )
                    )
                self._trigger_history.append(
                    VCDTriggerEvent("condition", self.current_time, cond)
                )
                self._current_level += 1
                break

        if self._current_level == self.trigger_levels:
            self._trigger_history.append(
                VCDTriggerEvent("trigger", self.current_time)
            )
            self._fire_trigger()
