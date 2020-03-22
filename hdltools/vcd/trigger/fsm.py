"""Trigger state machines."""

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

    def __init__(self, debug=False, **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
        self._levels = []
        self._current_level = 0
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

    def arm_trigger(self):
        """Arm trigger."""
        super().arm_trigger()
        self._current_level = 0

    def match_and_advance(self, var, value):
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
            self._trigger_history.append(
                VCDTriggerEvent("trigger", self.current_time)
            )
            self._fire_trigger()
