"""Trigger event."""

from typing import Optional
from hdltools.vcd import VCDObject
from hdltools.vcd.trigger import VCDTriggerDescriptor


class VCDTriggerEvent(VCDObject):
    """VCD trigger event."""

    EVENT_TYPES = ("condition", "trigger")

    def __init__(
        self,
        evt_type: str,
        time: int,
        evt: Optional[VCDTriggerDescriptor] = None,
    ):
        """Initialize."""
        if not isinstance(time, int):
            raise TypeError("time must be an integer")
        self._time = time
        if evt_type not in self.EVENT_TYPES:
            raise ValueError("invalid event type")
        self._type = evt_type

        if evt is None:
            self._evt = None
        elif not isinstance(evt, VCDTriggerDescriptor):
            raise TypeError("evt must be a VCDTriggerDescriptor object")
        else:
            self._evt = evt

    @property
    def time(self):
        """Get occurrence time."""
        return self._time

    @property
    def evt_type(self):
        """Get event type."""
        return self._type

    @property
    def evt(self):
        """Get trigger descriptor."""
        return self._evt
