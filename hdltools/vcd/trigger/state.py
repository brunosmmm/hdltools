"""Trigger state."""

from typing import Optional
from uuid import uuid1
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
