"""VCD Event tracker."""


from typing import Optional, Tuple, Dict
from colorama import Fore, Back, init
from uuid import uuid4
from hdltools.vcd import VCDObject
from hdltools.vcd.parser import BaseVCDParser, VCDParserError
from hdltools.vcd.trigger import VCDTriggerDescriptor
from hdltools.vcd.mixins.conditions import VCDConditionMixin
from hdltools.vcd.mixins.time import VCDTimeRestrictionMixin
from hdltools.vcd.trigger.condtable import ConditionTableTrigger

init(autoreset=True)

# an event is a VCDTriggerDescriptor


class VCDEvent(VCDObject):
    """VCD event."""

    def __init__(
        self,
        evt_type: str,
        time: int,
        duration: int = 0,
        uuid: Optional[str] = None,
    ):
        """Initialize."""
        self._type = evt_type
        self._time = time
        self._duration = duration
        if uuid is not None:
            self._uuid = uuid
        else:
            self._uuid = uuid4()

    @property
    def uuid(self):
        """Get uuid."""
        return self._uuid

    @property
    def evt_type(self):
        """Get event type."""
        return self._type

    @property
    def time(self):
        """Get occurence time."""
        return self._time

    @property
    def duration(self):
        """Get duration."""
        return self._duration

    @duration.setter
    def duration(self, value):
        """Set duration."""
        if not isinstance(value, int):
            raise TypeError("value must be integer")
        self._duration = value


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
                ConditionTableTrigger(
                    conditions=conds, evt_name=evt_name, oneshot=False
                ),
                None,
            ]
            for evt_name, conds in events.items()
        }
        # arm immediately
        for trigger, _ in self._evt_triggers.values():
            trigger.event_end_cb = self._evt_end_callback
            trigger.trigger_callback = self._evt_trigger_callback
            trigger.arm_trigger()

        # crude statistics
        self._event_counts = {}
        self._event_history = []

    @property
    def event_counts(self):
        """Get event counts."""
        return self._event_counts.copy()

    def _incr_evt_count(self, evt_name):
        """Increment event count."""
        if evt_name not in self._event_counts:
            self._event_counts[evt_name] = 1
        else:
            self._event_counts[evt_name] += 1

    def _log_evt_start(self, evt_type, time: Optional[int] = None):
        """Log event start."""
        if time is None:
            time = self.current_time
        new_evt = VCDEvent(evt_type, time)
        self._event_history.append(new_evt)
        return new_evt

    def _log_evt_end(self, evt_type, time: Optional[int] = None):
        """Log event end."""
        if time is None:
            time = self.current_time
        found_event = None
        for evt in self._event_history[::-1]:
            if evt.evt_type == evt_type:
                # found most recent, apply duration and move on
                found_event = evt
                evt.duration = time - evt.time
                break
        if found_event is None:
            raise RuntimeError("cannot end an event that has not started")

        return found_event

    def _evt_trigger_callback(self, trigger_fsm):
        """Event trigger callback."""
        # update last triggered time
        self._evt_triggers[trigger_fsm.evt_name][1] = self.current_time
        # increment count
        self._incr_evt_count(trigger_fsm.evt_name)
        # push into history
        new_evt = self._log_evt_start(
            trigger_fsm.evt_name, self.last_cycle_time
        )
        print(
            Back.RED
            + f"DEBUG: @{self.last_cycle_time}: evt fired: {trigger_fsm.evt_name} -> ({new_evt.uuid})"
        )

    def _evt_end_callback(self, trigger_fsm):
        """Event end callback."""
        evt_done = self._log_evt_end(
            trigger_fsm.evt_name, self.last_cycle_time
        )
        print(
            Back.RED
            + f"DEBUG: @{self.last_cycle_time}: evt deactivates after {evt_done.duration} cycles: {trigger_fsm.evt_name} -> ({evt_done.uuid})"
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
