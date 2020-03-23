"""Condition table-based trigger fsm."""


from typing import Optional, Tuple
from hdltools.vcd.trigger import VCDTriggerFSM, VCDTriggerDescriptor


class ConditionTableTrigger(VCDTriggerFSM):
    """Condition table trigger fsm.

    Unordered event-based trigger
    """

    def __init__(
        self,
        conditions: Optional[Tuple[VCDTriggerDescriptor]] = None,
        evt_name: Optional[str] = None,
        debug=False,
        oneshot=True,
        **kwargs,
    ):
        """Initialize."""
        super().__init__(**kwargs)
        self._condtable = {}
        self._evt_name = evt_name
        self._oneshot = oneshot
        self._event_end_cb = None

        if conditions is not None:
            for condition in conditions:
                self.add_condition(condition)

    @property
    def conditions_met(self):
        """Get number of conditions met."""
        met = 0
        for cond, state in self._condtable.items():
            if state:
                met += 1

        return met

    @property
    def unmet_conditions(self):
        """Get number of unmet conditions."""
        return len(self._condtable) - self.conditions_met

    @property
    def evt_name(self):
        """Get event name."""
        return self._evt_name

    @property
    def conditions(self):
        """Get conditions."""
        return self._condtable.keys()

    @property
    def oneshot(self):
        """Get oneshot."""
        return self._oneshot

    @oneshot.setter
    def oneshot(self, value):
        """Set oneshotness."""
        if not isinstance(value, bool):
            raise TypeError("value must be bool")
        if self.trigger_armed:
            raise RuntimeError("cannot change oneshot property while armed")

        self._oneshot = value

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

    def arm_trigger(self):
        """Arm trigger."""
        super().arm_trigger()
        # reset states
        if not self._condtable:
            raise RuntimeError("table empty; cannot arm")
        self._condtable = {evt: False for evt in self._condtable}

    def trigger_reset(self):
        """Reset trigger configuration."""
        super().trigger_reset()
        self._condtable = {}

    def add_condition(self, cond: VCDTriggerDescriptor):
        """Add condition."""
        if self.trigger_armed:
            raise RuntimeError("cannot add condition while trigger is armed")
        if cond in self._condtable:
            raise ValueError("condition is already in condition table")
        if not isinstance(cond, VCDTriggerDescriptor):
            raise TypeError("cond must be a VCDTriggerDescriptor object")
        self._condtable[cond] = False

    def remove_condition(self, cond: VCDTriggerDescriptor):
        """Remove condition."""
        if self.trigger_armed:
            raise RuntimeError(
                "cannot remove condition while trigger is armed"
            )
        del self._condtable[cond]

    def __len__(self):
        """Get table length."""
        return len(self._condtable)

    def __getitem__(self, key: VCDTriggerDescriptor) -> bool:
        """Get condition state."""
        return self._condtable[key]

    def _event_ends(self):
        """Event ends."""
        self.disarm_trigger()
        if self._event_end_cb:
            self._event_end_cb(self)

    def advance(self, cond, value):
        """Advance value directly without variable name matching."""
        if self.trigger_armed is False:
            return (False, None)
        if cond.match_value(value):
            self._condtable[cond] = True
            return (True, True)
        else:
            self._condtable[cond] = False
            return (True, False)

    def check_and_fire(self):
        """Check current state and fire."""
        if self.unmet_conditions == 0 and self.triggered is False:
            # done (event start)
            self._fire_trigger(self.oneshot)

        if (
            not self.oneshot
            and self.unmet_conditions != 0
            and self.triggered is True
        ):
            # event ends
            self._event_ends()

    def match_and_advance(self, var, value):
        """Update condition states."""
        if self.trigger_armed is False:
            return
        updated_values = {}
        for cond, state in self._condtable.items():
            if cond.match_var(var.scope, var.name, var.identifiers[0]):
                # condition in table
                if cond.match_value(value):
                    updated_values[cond] = True
                    print(f"DEBUG: cond {cond} -> TRUE")
                else:
                    updated_values[cond] = False
                    print(f"DEBUG: cond {cond} -> FALSE")

        # save updated values
        self._condtable.update(updated_values)

        # check current state and fire
        if self.unmet_conditions == 0:
            # done
            self._fire_trigger()
