"""Trigger state machines."""

from hdltools.vcd.trigger import (
    VCDTriggerDescriptor,
    VCDTriggerError,
    VCDTriggerEvent,
)


class BranchingTrigger:
    """Branching trigger state machine."""

    def __init__(self, **kwargs):
        """Initialize."""


class SimpleTrigger:
    """Legacy trigger state machine."""

    def __init__(self, debug=False):
        """Initialize."""
        self._levels = []
        self._current_level = 0
        self._trigger_cb = None
        self._armed = False
        self._triggered = False
        self._trigger_history = []
        self._debug = debug

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

    @property
    def trigger_history(self):
        """Get trigger event history."""
        return self._trigger_history

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

    def match_and_advance(self, state, var, value):
        """Value change hook."""
        if self._armed is False:
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
            self.disarm_trigger()
            self._triggered = True
            self._trigger_history.append(
                VCDTriggerEvent("trigger", self.current_time)
            )
            if self._trigger_cb is not None:
                self._trigger_cb()
