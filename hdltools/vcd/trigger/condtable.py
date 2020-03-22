"""Condition table-based trigger fsm."""

from hdltools.vcd.trigger import VCDTriggerFSM


class ConditionTableTrigger(VCDTriggerFSM):
    """Condition table trigger fsm.

    Unordered event-based trigger
    """

    def __init__(self, debug=False):
        """Initialize."""
        super().__init__()
        self._condtable = {}

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

    def trigger_reset(self):
        """Reset trigger configuration."""
        super().trigger_reset()
        self._condtable = []

    def add_condition(self, cond):
        """Add condition."""
        if self.trigger_armed:
            raise RuntimeError("cannot add condition while trigger is armed")
        if cond in self._condtable:
            raise ValueError("condition is already in condition table")
        self._condtable[cond] = False

    def remove_condition(self, cond):
        """Remove condition."""
        if self.trigger_armed:
            raise RuntimeError(
                "cannot remove condition while trigger is armed"
            )
        del self._condtable[cond]

    def match_and_advance(self, var, value):
        """Update condition states."""
        updated_values = {}
        for cond, state in self._condtable.items():
            if cond.scope == var.scope and cond.name == var.name:
                # condition in table
                if cond.value.match(value):
                    updated_values[cond] = True
                else:
                    updated_values[cond] = False

        # save updated values
        self._condtable = updated_values

        # check current state and fire
        if self.unmet_conditions == 0:
            # done
            self._fire_trigger()
