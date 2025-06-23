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
        debug=False,
        oneshot=True,
        **kwargs,
    ):
        """Initialize."""
        super().__init__(**kwargs)
        self._condtable = {}
        self._oneshot = oneshot

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
    def conditions(self):
        """Get conditions."""
        return self._condtable.keys()

    @VCDTriggerFSM.sensitivity_list.getter
    def sensitivity_list(self):
        """Get current sensitivity list."""
        return self.conditions

    @VCDTriggerFSM.global_sensitivity_list.getter
    def global_sensitivity_list(self):
        """Get global sensitivity list."""
        return self.conditions

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

    def arm_trigger(self, reset_conds=False):
        """Arm trigger."""
        super().arm_trigger()
        # reset states
        if not self._condtable:
            raise RuntimeError("table empty; cannot arm")
        if reset_conds:
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

    def advance(self, cond, value, time):
        """Advance value directly without variable name matching."""
        if self.trigger_armed is False:
            return (False, None, False)
        if cond.match_value(value):
            if self._condtable[cond] is False:
                changed = True
                self._condtable[cond] = True
            else:
                changed = False
            return (changed, True, False)
        else:
            if self._condtable[cond]:
                changed = True
                self._condtable[cond] = False
            else:
                changed = False
            return (changed, False, False)

    def check_and_fire(self, time=None):
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

    def match_and_advance(self, var, value, time=None):
        """Update condition states."""
        if self.trigger_armed is False:
            return
        updated_values = {}
        for cond, state in self._condtable.items():
            # Support both old (identifiers[0]) and new (id) variable formats
            var_id = var.identifiers[0] if hasattr(var, 'identifiers') and var.identifiers else getattr(var, 'id', None)
            var_scope = getattr(var, 'scope', None)  # Old format
            var_name = getattr(var, 'name', '')
            
            # For efficient storage, scope info might be in reference, but we rely on var_id matching
            if cond.match_var(var_scope, var_name, var_id):
                # condition in table
                # Strip 'b' prefix from VCD binary values
                clean_value = value.lstrip('b') if isinstance(value, str) and value.startswith('b') else value
                if cond.match_value(clean_value):
                    updated_values[cond] = True
                else:
                    updated_values[cond] = False

        # save updated values
        self._condtable.update(updated_values)

        # check current state and fire
        if self.unmet_conditions == 0:
            # done
            self._fire_trigger()
