"""VCD Event tracker."""


from typing import Dict, Optional, Tuple, Type, Union
from uuid import uuid4

from colorama import Back, Fore, init
from hdltools.vcd import VCDObject
from hdltools.vcd.mixins.conditions import VCDConditionMixin
from hdltools.vcd.mixins.time import VCDTimeRestrictionMixin
from hdltools.vcd.parser import BaseVCDParser, CompiledVCDParser
from hdltools.vcd.trigger import VCDTriggerDescriptor
from hdltools.vcd.trigger.condtable import ConditionTableTrigger
from hdltools.vcd.trigger.fsm import SimpleTrigger

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
        """Initialize.

        :param evt_type: Event type
        :param time: Event start time
        :param duration: Event duration
        :param uuid: Optional unique identifier
        """
        self._type = evt_type
        self._time = time
        self._duration = duration
        if uuid is not None:
            self._uuid = uuid
        else:
            self._uuid = uuid4()

    @property
    def uuid(self) -> Union[None, str]:
        """Get uuid."""
        return self._uuid

    @property
    def evt_type(self) -> str:
        """Get event type."""
        return self._type

    @property
    def time(self) -> int:
        """Get occurence time."""
        return self._time

    @property
    def duration(self) -> int:
        """Get duration."""
        return self._duration

    @duration.setter
    def duration(self, value: int):
        """Set duration.

        :param value: The event duration
        """
        if not isinstance(value, int):
            raise TypeError("value must be integer")
        self._duration = value

    @property
    def serialized(self) -> Dict[str, Union[str, int]]:
        """Get serializeable version."""
        return {
            "uuid": str(self.uuid),
            "evt_type": self.evt_type,
            "time": self.time,
            "duration": self.duration,
        }


def get_tracker_class(parser_class: Type) -> Type:
    """Build event tracker class dynamically.

    :param parser_class: Parser base class
    """

    class VCDEventTracker(
        parser_class, VCDConditionMixin, VCDTimeRestrictionMixin
    ):
        """Event tracker."""

        def __init__(
            self,
            events: Dict[str, Tuple[Tuple[VCDTriggerDescriptor], str]],
            **kwargs,
        ):
            """Initialize.

            :param events: Dictionary of events
            :param kwargs: Any other parser kwargs
            """
            super().__init__(**kwargs)
            self._events = events
            self._evt_triggers = {}
            self._compile_triggers(events)
            # arm immediately
            for trigger, _ in self._evt_triggers.values():
                trigger.event_start_cb = self._evt_start_callback
                trigger.event_end_cb = self._evt_end_callback
                trigger.trigger_callback = self._evt_trigger_callback
                trigger.event_timeout_cb = self._evt_timeout_callback
                trigger.arm_trigger()

            # crude statistics
            self._event_counts = {}
            self._event_cycles = {}
            self._event_history = []

        def _compile_triggers(self, events):
            """Build trigger array."""
            for evt_name, ((cond, mode), opts) in events.items():
                if mode == "&&":
                    self._evt_triggers[evt_name] = [
                        ConditionTableTrigger(
                            conditions=cond, evt_name=evt_name, oneshot=False
                        ),
                        None,
                    ]
                elif mode == "=>":
                    trigger = SimpleTrigger(levels=cond, evt_name=evt_name)
                    trigger.state_timeout = opts.get("timeout")
                    self._evt_triggers[evt_name] = [trigger, None]
                else:
                    raise RuntimeError("invalid mode in trigger description")

        @property
        def event_counts(self):
            """Get event counts."""
            return self._event_counts.copy()

        @property
        def event_cycles(self):
            """Get total cycle count per event."""
            return self._event_cycles.copy()

        @property
        def event_history(self):
            """Get event history."""
            return self._event_history

        def _incr_evt_count(self, evt):
            """Increment event count."""
            if evt.evt_type not in self._event_counts:
                self._event_counts[evt.evt_type] = 1
                self._event_cycles[evt.evt_type] = evt.duration
            else:
                self._event_counts[evt.evt_type] += 1
                self._event_cycles[evt.evt_type] += evt.duration

        def _log_evt_start(
            self,
            evt_type,
            time: Optional[int] = None,
            uuid: Optional[str] = None,
        ):
            """Log event start."""
            if time is None:
                time = self.current_time
            new_evt = VCDEvent(evt_type, time, uuid=uuid)
            self._event_history.append(new_evt)
            return new_evt

        def _log_evt_end(
            self,
            evt_type,
            time: Optional[int] = None,
            uuid: Optional[str] = None,
        ):
            """Log event end."""
            if time is None:
                time = self.current_time
            found_event = None
            for evt in self._event_history[::-1]:
                # prefer uuid
                if (
                    (uuid is not None and evt.uuid == uuid)
                    or evt.evt_type
                    and evt.evt_type == evt_type
                ):
                    # found most recent, apply duration and move on
                    found_event = evt
                    evt.duration = time - evt.time
                    break
            if found_event is None:
                raise RuntimeError("cannot end an event that has not started")

            return found_event

        def _remove_evt_history(self, uuid: str):
            """Remove event from history."""
            found = False
            for idx, evt in enumerate(self._event_history[::-1]):
                if uuid == evt.uuid:
                    found = True
                    break

            if found is False:
                raise RuntimeError(f"event not found: {uuid}")
            del self._event_history[len(self._event_history) - idx - 1]
            return evt

        def _evt_started_or_fired(self, trigger_fsm):
            """Handle similar events."""
            # update last triggered time
            self._evt_triggers[trigger_fsm.evt_name][1] = self.current_time
            # push into history
            if trigger_fsm.event_ending:
                return self._log_evt_end(
                    trigger_fsm.evt_name,
                    self.last_cycle_time,
                    trigger_fsm.current_evt,
                )
            return self._log_evt_start(
                trigger_fsm.evt_name,
                self.last_cycle_time,
                trigger_fsm.current_evt,
            )

        def _evt_start_callback(self, trigger_fsm):
            """Event start trigger callback."""
            new_evt = self._evt_started_or_fired(trigger_fsm)
            if self._debug:
                print(
                    Back.YELLOW
                    + Fore.BLACK
                    + f"DEBUG: @{self.last_cycle_time}: evt starts: "
                    f"{trigger_fsm.evt_name} -> ({new_evt.uuid})"
                )

        def _evt_trigger_callback(self, trigger_fsm):
            """Event trigger callback."""
            # increment count
            evt = self._evt_started_or_fired(trigger_fsm)
            if trigger_fsm.event_ending:
                self._incr_evt_count(evt)
            if self._debug:
                if trigger_fsm.event_ending:
                    end_msg = f" after {evt.duration} cycles"
                else:
                    end_msg = ""
                print(
                    Back.YELLOW
                    + Fore.BLACK
                    + f"DEBUG: @{self.last_cycle_time}: evt fired{end_msg}: "
                    f"{trigger_fsm.evt_name} -> ({evt.uuid})"
                )

        def _evt_end_callback(self, trigger_fsm):
            """Event end callback."""
            evt_done = self._log_evt_end(
                trigger_fsm.evt_name,
                self.last_cycle_time,
                trigger_fsm.current_evt,
            )
            self._incr_evt_count(evt_done)
            if self._debug:
                print(
                    Back.YELLOW
                    + Fore.BLACK
                    + f"DEBUG: @{self.last_cycle_time}: evt deactivates after"
                    f" {evt_done.duration} cycles: {trigger_fsm.evt_name} ->"
                    f" ({evt_done.uuid})"
                )

        def _evt_timeout_callback(self, trigger_fsm):
            """Event timeout callback."""
            # rollback started event
            evt = self._remove_evt_history(trigger_fsm.current_evt)
            if self._debug:
                print(
                    Back.RED
                    + Fore.BLACK
                    + f"DEBUG: @{self.last_cycle_time}: evt timeout: "
                    f"{trigger_fsm.evt_name} -> ({evt.uuid})"
                )

        def _state_change_handler(self, old_state, new_state):
            """Detect state transition."""
            super()._state_change_handler(old_state, new_state)
            # when header state finishes, we have list of variables
            if old_state == "header":
                # add VCD variable identifiers to condition table elements
                for _, (condtable, _) in self._evt_triggers.items():
                    for cond in condtable.global_sensitivity_list:
                        # post-process now
                        candidates = self.variable_search(
                            cond.name, cond.scope, True
                        )
                        if not candidates:
                            raise RuntimeError("cannot locate VCD variable")
                        # associate with first candidate
                        cond.vcd_var = list(candidates)[0].identifiers[0]
                if self._debug:
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
                for cond in condtable.sensitivity_list:
                    # pick variables directly for speed
                    var = self.variables[cond.vcd_var]
                    if var.last_changed == self.last_cycle_time:
                        _changed, state, stop = condtable.advance(
                            cond, var.value, self.last_cycle_time
                        )
                        if _changed:
                            changed.append((cond, state))
                        if stop:
                            break

                if changed:
                    if self._debug:
                        print(
                            Fore.CYAN
                            + f"DEBUG: @{self.last_cycle_time}: table"
                            f" {condtable.triggerid} changes:"
                        )
                        for cond, state in changed:
                            msg_color = (
                                Fore.RED if state is False else Fore.GREEN
                            )
                            print(msg_color + f"DEBUG: cond {cond} -> {state}")

                # check and fire trigger. NOTE: potentially much slower in here
                condtable.check_and_fire(self.last_cycle_time)

        def initial_value_handler(self, stmt, fields):
            """Handle initial value assignment."""
            var = self.variables[fields["var"]]
            var.value = fields["value"]

        def value_change_handler(self, stmt, fields):
            """Handle value change."""
            var = self.variables[fields["var"]]
            var.value = fields["value"]
            var.last_changed = self.current_time
            if (
                self.time_valid is False
                or self.waiting_precondition
                and self.current_time > 0
            ):
                return
            # update local variable value

    return VCDEventTracker


VCDEventTrackerLegacy = get_tracker_class(BaseVCDParser)
VCDEventTrackerCompiled = get_tracker_class(CompiledVCDParser)
