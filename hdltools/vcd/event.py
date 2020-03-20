"""VCD Event tracker."""

from typing import Tuple
from hdltools.vcd.parser import BaseVCDParser, VCDParserError
from hdltools.vcd.trigger import VCDTriggerDescriptor
from hdltools.vcd.mixins.condition import VCDConditionMixin
from hdltools.vcd.mixins.time import VCDTimeRestrictionMixin
from hdltools.vcd.trigger.fsm import SimpleTrigger

# an event is a VCDTriggerDescriptor


class VCDEventTracker(
    BaseVCDParser, VCDConditionMixin, VCDTimeRestrictionMixin
):
    """Event tracker."""

    def __init__(self, events: Tuple[VCDTriggerDescriptor], **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
        for event in events:
            if not isinstance(event, VCDTriggerDescriptor):
                raise TypeError("events must be VCDTriggerDescriptor objects")

        self._events = events
        self._evt_trigger = SimpleTrigger()
        # add events, only one level
        self._evt_trigger.add_trigger_level(events)
        # arm immediately
        self._evt_trigger.trigger_callback = self._evt_trigger_callback
        self._evt_trigger.arm_trigger()

    def _evt_trigger_callback(self):
        """Event trigger callback."""
        # rearm immediately
        self._evt_trigger.arm_trigger()

    def value_change_handler(self, stmt, fields):
        """Handle value change."""
        if self.time_valid is False or self.waiting_precondition:
            return

        # feed event trigger
        var = self.variables[fields["var"]]
        self._evt_trigger.match_and_advance(var, fields["value"])
