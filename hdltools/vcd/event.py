"""VCD Event tracker."""


from typing import Tuple, Dict
from colorama import Fore, Back, init
from hdltools.vcd.parser import BaseVCDParser, VCDParserError
from hdltools.vcd.trigger import VCDTriggerDescriptor
from hdltools.vcd.mixins.conditions import VCDConditionMixin
from hdltools.vcd.mixins.time import VCDTimeRestrictionMixin
from hdltools.vcd.trigger.condtable import ConditionTableTrigger

init(autoreset=True)

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
            evt_name: [
                ConditionTableTrigger(conditions=conds, evt_name=evt_name),
                None,
            ]
            for evt_name, conds in events.items()
        }
        # arm immediately
        for trigger, _ in self._evt_triggers.values():
            trigger.trigger_callback = self._evt_trigger_callback
            trigger.arm_trigger()

    def _evt_trigger_callback(self, trigger_fsm):
        """Event trigger callback."""
        # update last triggered time
        self._evt_triggers[trigger_fsm.evt_name][1] = self.current_time
        print(
            Back.RED
            + f"DEBUG: {self.last_cycle_time}: evt fired: {trigger_fsm.evt_name}"
        )

    def _state_change_handler(self, old_state, new_state):
        """Detect state transition."""
        super()._state_change_handler(old_state, new_state)
        # when header state finishes, we have list of variables
        if old_state == "header":
            # add VCD variable identifiers to condition table elements
            for _, (condtable, _) in self._evt_triggers.items():
                for cond in condtable.conditions:
                    # post-process now
                    candidates = self.variable_search(
                        cond.name, cond.scope, True
                    )
                    if not candidates:
                        raise RuntimeError("cannot locate VCD variable")
                    # associate with first candidate
                    cond.vcd_var = list(candidates)[0].identifiers[0]
            print("DEBUG: header parsing completed")

    def clock_change_handler(self, time):
        """Handle time."""
        if time == 0:
            return
        for condtable, _ in self._evt_triggers.values():
            # re-arm
            if condtable.trigger_armed is False:
                condtable.arm_trigger()
        for condtable, _ in self._evt_triggers.values():
            # update consolidated values
            changed = []
            for cond in condtable.conditions:
                # pick variables directly for speed
                var = self.variables[cond.vcd_var]
                if var.last_changed == self.last_cycle_time:
                    _changed, state = condtable.advance(cond, var.value)
                    if _changed:
                        changed.append((cond, state))

            if changed:
                print(
                    Fore.CYAN
                    + f"DEBUG: @{time}: table {condtable.triggerid} changes:"
                )
                for cond, state in changed:
                    msg_color = Fore.RED if state is False else Fore.GREEN
                    print(msg_color + f"DEBUG: cond {cond} -> {state}")

            # check and fire trigger
            condtable.check_and_fire()
            # for var in self.variables.values():
            #     # print(var.value)
            #     if var.last_changed == self.last_cycle_time:
            #         condtable.match_and_advance(var, var.value)

    def initial_value_handler(self, stmt, fields):
        """Handle initial value assignment."""
        var = self.variables[fields["var"]]
        var.value = fields["value"]

    def value_change_handler(self, stmt, fields):
        """Handle value change."""
        if self.time_valid is False or self.waiting_precondition:
            return
        # update local variable value
        var = self.variables[fields["var"]]
        var.value = fields["value"]
        var.last_changed = self.current_time
        # for trigger, _ in self._evt_triggers.values():
        #     trigger.match_and_advance(var, fields["value"])
