"""Finite state machines."""

import inspect
import math
import re
from collections import OrderedDict
from functools import wraps

from hdltools.abshdl.assign import HDLAssignment
from hdltools.abshdl.comment import HDLComment
from hdltools.abshdl.ifelse import HDLIfElse
from hdltools.abshdl.macro import HDLMacro, HDLMacroValue
from hdltools.abshdl.switch import HDLCase, HDLSwitch
from hdltools.hdllib.patterns import ClockedBlock


class FSMInputError(Exception):
    """FSM Input signal error."""


class FSMInvalidStateError(Exception):
    """Invalid FSM state error."""


class FSMProxy:
    """Proxy object for FSM inference."""

    def __init__(
        self,
        fsm_type,
        instance_name,
        initial,
        signal_scope,
        state_methods,
        state_var_name,
    ):
        """Initialize."""
        self.initial = initial
        self.signal_scope = signal_scope
        self._type = fsm_type
        self.name = instance_name
        self.state_var_name = state_var_name
        self._state_transitions = {}
        self._current_state = initial
        self._state_methods = state_methods
        self.__infer_fsm()

    @property
    def state(self):
        """Current state."""
        raise NotImplementedError

    @property
    def fsm_type(self):
        """Get fsm type."""
        return self._type

    @state.setter
    def state(self, next_state):
        """Set current state."""
        if self._current_state is None:
            self.current_state = self.initial
        if self._current_state not in self._state_transitions:
            self._state_transitions[self._current_state] = set()

        cur_trans = self._state_transitions[self._current_state]

        if next_state not in self._state_methods:
            raise FSMInvalidStateError(
                "invalid state name: {}".format(next_state)
            )

        cur_trans |= set([next_state])

    def __infer_fsm(self):
        """Infer FSM."""
        for state_name, (method, inputs) in self._state_methods.items():
            self._current_state = state_name
            for _input in inputs:
                signal = self.signal_scope[_input]
                for i in range(0, 2 ** len(signal)):
                    method(self, i)
            if len(inputs) == 0:
                method(self)

        return self._state_transitions

    def get_transition_map(self):
        """Get map of state transitions."""
        return self._state_transitions


class FSM:
    """Finite state machine."""

    @classmethod
    def _infer_fsm(
        cls, signal_scope, states, initial_state, instance_name, state_var_name
    ):
        # verify that signals are in scope.
        for state_name, (method, inputs) in states.items():
            for _input in inputs:
                if _input not in signal_scope:
                    raise FSMInputError(
                        "in state '{}': input signal '{}' is not available in scope".format(
                            state_name, _input
                        )
                    )
        fsm_object = FSMProxy(
            cls.__name__,
            instance_name,
            initial_state,
            signal_scope,
            states,
            state_var_name,
        )
        return fsm_object

    @classmethod
    def _collect_states(cls):
        state_methods = {}
        for method_name, method in inspect.getmembers(cls):
            cls_name = cls.__name__
            m = re.match(
                r"_{}__state_([a-zA-Z0-9_]+)".format(cls_name), method_name
            )
            if m is not None:
                # found a state
                if inspect.ismethod(method) or inspect.isfunction(method):
                    args = set(inspect.getfullargspec(method).args)
                    input_list = args - set(["self"])
                    state_methods[m.group(1)] = (method, input_list)

        return state_methods

    def __call__(self, fn):
        """Decorate."""

        @wraps(fn)
        def wrapper_FSM(*args, **kwargs):
            # do stuff
            seq, const = self.get(
                self.clk,
                self.rst,
                self.state_var,
                self.initial,
                self.edge,
                self.lvl,
                self._signal_scope,
            )
            fn(seq, const, *args, **kwargs)
            return (seq, const)

        return wrapper_FSM

    @classmethod
    def get(
        cls,
        clk,
        rst,
        state_var,
        initial,
        edge="rise",
        lvl=1,
        instance_name=None,
        _signal_scope=None,
    ):
        """Get sequential block."""
        seq = ClockedBlock.get(clk, edge)
        const = []
        rst_if = HDLIfElse(rst == lvl, tag="rst_if")
        seq.add(rst_if)

        # add cases
        states = cls._collect_states()
        cases = []
        state_mapping = OrderedDict()

        fsm = cls._infer_fsm(
            _signal_scope, states, initial, instance_name, state_var
        )

        # set state variable size
        state_var.set_size(int(math.ceil(math.log2(float(len(states))))))

        # add switch
        sw = HDLSwitch(state_var)
        rst_if.add_to_else_scope(sw)

        i = 0
        for state in states:
            state_mapping[state] = i
            case = HDLCase(HDLMacroValue(state), tag=f"__autogen_case_{state}")
            case.add_to_scope(
                HDLComment(
                    f"case {state}",
                    tag=f"__autogen_case_{state}",
                )
            )
            cases.append(case)
            sw.add_case(case)
            const.append(HDLMacro(state, i))
            i += 1

        if initial in state_mapping:
            rst_if.add_to_if_scope(
                HDLAssignment(state_var, HDLMacroValue(initial))
            )
        else:
            raise RuntimeError("initial state not specified")

        # PROCESS STATES
        return (seq, const, fsm)
