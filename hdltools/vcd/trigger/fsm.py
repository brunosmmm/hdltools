"""Branching trigger state machine."""

from typing import Optional, Dict
from uuid import uuid1
from hdltools.vcd.trigger import VCDTriggerDescriptor
from hdltools.vcd import VCDScope


class TriggerState:
    """Abstract class for trigger states."""

    def __init__(self, name: Optional[str] = None):
        """Initialize."""
        self._name = uuid1() if name is None else name

    @property
    def name(self):
        """Get name."""
        return self._name

    def match(self, scope: VCDScope, name: str, value: str) -> bool:
        """Match condition against value."""
        return self._condition.match(scope, name, value)

    def match_and_fire(self, scope: VCDScope, name: str, value: str) -> bool:
        """Match and move to next state."""
        raise NotImplementedError


class TriggerTarget(TriggerState):
    """A trigger final state, or target."""

    def __init__(self, condition: VCDTriggerDescriptor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(condition, VCDTriggerDescriptor):
            raise TypeError("condition must be a VCDTriggerDescriptor object")
        self._callback = None
        self._cond = condition

    @property
    def condition(self):
        """Get condition."""
        return self._cond

    @property
    def callback(self):
        """Get callback."""
        return self._callback

    @callback.setter
    def callback(self, cb):
        """Set callback."""
        if not callable(cb):
            raise TypeError("cb must be a callable")
        self._callback = cb

    def match_and_fire(self, scope: VCDScope, name: str, value: str):
        """Match and fire trigger."""
        if self.match(scope, name, value):
            if self._callback:
                self._callback()
            return None

        return self


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


class BranchingTrigger:
    """Trigger state machine."""

    def __init__(self, **kwargs):
        """Initialize."""
