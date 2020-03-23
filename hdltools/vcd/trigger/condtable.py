"""Condition table-based trigger fsm."""


from typing import Optional, Tuple, Union
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
    ):
        """Initialize."""
        super().__init__()
        self._condtable = {}
        self._evt_name = evt_name

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

    def advance(self, cond, value):
        """Advance value directly without variable name matching."""
        if cond.match_value(value):
            self._condtable[cond] = True
            print(f"DEBUG: cond {cond} -> TRUE")
        else:
            self._condtable[cond] = False
            print(f"DEBUG: cond {cond} -> FALSE")
        # check current state and fire
        if self.unmet_conditions == 0:
            # done
            self._fire_trigger()

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
