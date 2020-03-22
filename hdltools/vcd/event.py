"""VCD Event tracker."""


from typing import Tuple, Dict
from hdltools.vcd.parser import BaseVCDParser, VCDParserError
from hdltools.vcd.trigger import VCDTriggerDescriptor
from hdltools.vcd.mixins.conditions import VCDConditionMixin
from hdltools.vcd.mixins.time import VCDTimeRestrictionMixin
from hdltools.vcd.trigger.condtable import ConditionTableTrigger

# an event is a VCDTriggerDescriptor


class VCDEventTracker(
    BaseVCDParser, VCDConditionMixin, VCDTimeRestrictionMixin
):
    """Event tracker."""

    def __init__(
        self, events: Dict[str, Tuple[VCDTriggerDescriptor]], **kwargs
    ):
        """Initialize."""
        super().__init__(**kwargs)
        self._events = events
        self._evt_triggers = {
            evt_name: ConditionTableTrigger(conditions=conds)
            for evt_name, conds in events.items()
        }
        # arm immediately
        for trigger in self._evt_triggers.values():
            trigger.trigger_callback = self._evt_trigger_callback
            trigger.arm_trigger()

    def _evt_trigger_callback(self, trigger_fsm):
        """Event trigger callback."""
        # rearm immediately
        trigger_fsm.arm_trigger()

    def value_change_handler(self, stmt, fields):
        """Handle value change."""
        if self.time_valid is False or self.waiting_precondition:
            return

        # feed event triggers
        var = self.variables[fields["var"]]
        for trigger in self._evt_triggers.values():
            trigger.match_and_advance(var, fields["value"])
