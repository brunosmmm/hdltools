"""Trigger target."""

from hdltools.vcd.trigger.state import TriggerState
from hdltools.vcd.scope import VCDScope
from hdltools.vcd.trigger import VCDTriggerDescriptor


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
