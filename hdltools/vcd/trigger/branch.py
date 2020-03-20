"""Trigger branch or intermediate state."""

from typing import Dict
from hdltools.vcd.trigger.state import TriggerState
from hdltools.vcd.trigger import VCDTriggerDescriptor


class TriggerBranch(TriggerState):
    """A state with many possible targets."""

    def __init__(
        self,
        conditions: Dict[VCDTriggerDescriptor, TriggerState],
        *args,
        **kwargs
    ):
        """Initialize."""
        super().__init__(*args, **kwargs)
        self._conditions = conditions

    @property
    def conditions(self):
        """Get conditions."""
        return self._conditions

    def match_and_fire(self, scope, name, value):
        """Match and change state."""
        for cond, next_state in self._conditions.items():
            if cond.match(scope, name, value) is True:
                return next_state

        # no match
        return self
