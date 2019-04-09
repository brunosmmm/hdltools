"""Common HDL patterns."""

from ..abshdl.seq import HDLSequentialBlock
from ..abshdl.ifelse import HDLIfElse
from ..abshdl.sens import HDLSensitivityDescriptor, HDLSensitivityList
from ..abshdl.scope import HDLScope
from ..abshdl.module import HDLModule, HDLModulePort
from ..abshdl.switch import HDLSwitch, HDLCase
from ..abshdl.macro import HDLMacro, HDLMacroValue
from ..abshdl.assign import HDLAssignment
from ..abshdl.comment import HDLComment
from functools import wraps
from collections import OrderedDict
import inspect
import re
import math


class InvalidStateError(Exception):
    """Invalid FSM state error."""

    pas


def get_sequential_block(sens_list, *stmts, **kwargs):
    """Get an unpopulated sequential block."""
    sens = HDLSensitivityList(sens_list)
    seq = HDLSequentialBlock(sens, **kwargs)
    seq.add(*stmts)

    return seq


def get_clocked_block(clock_signal, edge, *stmts, **kwargs):
    """Get a clocked block, unpopulated."""
    clk_sens = HDLSensitivityDescriptor(edge, clock_signal)
    sens = HDLSensitivityList(clk_sens)
    seq = HDLSequentialBlock(sens, **kwargs)
    seq.add(*stmts)

    return seq


def get_clock_rst_block(
    clock_signal, rst_signal, clk_edge, rst_lvl, rst_stmts, stmts=None, **kwargs
):
    """Get a clocked block, with synchronous reset."""
    clk_sens = HDLSensitivityDescriptor(clk_edge, clock_signal)
    sens = HDLSensitivityList(clk_sens)
    seq = HDLSequentialBlock(sens, **kwargs)
    ifelse = get_reset_if_else(rst_signal, rst_lvl, rst_stmts, stmts, **kwargs)
    seq.add(ifelse)

    return seq


def get_any_sequential_block(*stmts, **kwargs):
    """Get a block that is sensitive to anything."""
    any_sens = HDLSensitivityDescriptor("any")
    sens = HDLSensitivityList(any_sens)
    seq = HDLSequentialBlock(sens, **kwargs)
    seq.add(*stmts)

    return seq


def get_reset_if_else(rst_signal, rst_lvl, rst_stmts, stmts=None, **kwargs):
    """Get reset if-else."""
    if rst_lvl == 0:
        rst_cmp = rst_signal == 0
    else:
        rst_cmp = rst_signal == 1
    ifelse = HDLIfElse(rst_cmp, if_scope=rst_stmts, else_scope=stmts)

    return ifelse


def get_module(name, inputs=None, outputs=None):
    """Get a module."""
    module_ports = []
    for inp in inputs:
        module_ports.append(HDLModulePort("in", *inp))
    for out in outputs:
        module_ports.append(HDLModulePort("out", *out))

    mod = HDLModule(name, ports=module_ports)
    return mod


class SequentialBlock:
    """Sequential block decorator."""

    def __init__(self, *args):
        """Initialize."""
        self.signals = args

    def __call__(self, fn):
        """Decorate."""

        @wraps(fn)
        def wrapper_SequentialBlock(*args):
            seq = self.get(*self.signals)
            fn(seq, *args)
            return seq

        return wrapper_SequentialBlock

    @staticmethod
    def get(*args):
        """Get sequential block."""
        sens_descrs = []
        for arg in args:
            if isinstance(arg, (tuple, list)):
                sens_descrs.append(HDLSensitivityDescriptor(*arg))
            else:
                sens_descrs.append(HDLSensitivityDescriptor("rise", arg))
            sens_list = HDLSensitivityList(*sens_descrs)
        seq = HDLSequentialBlock(sens_list)
        return seq


class ClockedBlock(SequentialBlock):
    """Clocked sequential block."""

    def __init__(self, clk, edge="rise"):
        """Initialize."""
        self.clk = clk
        self.edge = edge

    def __call__(self, fn):
        """Decorate."""

        @wraps(fn)
        def wrapper_ClockedBlock(*args):
            seq = self.get(self.clk, self.edge)
            fn(seq, *args)
            return seq

        return wrapper_ClockedBlock

    @staticmethod
    def get(clk, edge="rise"):
        """Get Clocked block."""
        sens_list = HDLSensitivityList(HDLSensitivityDescriptor(edge, clk))
        seq = HDLSequentialBlock(sens_list)
        return seq


class ClockedRstBlock(ClockedBlock):
    """Clocked sequential block with reset."""

    def __init__(self, clk, rst, clk_edge="rise", rst_lvl=1):
        """Initialize."""
        self.rst = rst
        self.lvl = rst_lvl
        self.clk = clk
        self.edge = clk_edge

    def __call__(self, fn):
        """Decorate."""

        @wraps(fn)
        def wrapper_ClockedRstBlock(*args, **kwargs):
            # do stuff
            seq = self.get(self.clk, self.rst, self.edge, self.lvl)
            fn(seq, *args, **kwargs)
            return seq

        return wrapper_ClockedRstBlock

    @staticmethod
    def get(clk, rst, edge="rise", lvl=1):
        """Get sequential block."""
        seq = ClockedBlock.get(clk, edge)
        rst_if = HDLIfElse(rst == lvl, tag="rst_if")
        seq.add(rst_if)
        return seq


class FSM(ClockedBlock):
    """Finite state machine."""

    def __init__(
        self, clk, rst, state_var, initial, clk_edge="rise", rst_lvl=1, **kwargs
    ):
        """Initialize."""
        super().__init__(clk, rst, clk_edge, rst_lvl)
        self.initial = initial
        self.state_var = state_var
        self._signal_scope = kwargs
        self._state_transitions = {}
        self._current_state = None
        self._state_names = self._collect_states()

    @property
    def state(self):
        """Current state."""
        raise NotImplementedError

    @state.setter
    def state(self, next_state):
        """Set current state."""
        if self._current_state is None:
            self.current_state = self.initial
        if self._current_state not in self._state_transitions:
            self._state_transitions[self._current_state] = set()

        cur_trans = self._state_transitions[self._current_state]

        if next_state not in self._state_names:
            raise InvalidStateError("invalid state name: {}".format(next_state))

        cur_trans |= set([next_state])

    def _infer_fsm(self):
        """Infer FSM."""
        for state_name, method in self._state_names.items():
            # TODO call method, cant because arguments are unknown
            # method()
            pass

        return self._state_transitions

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
                    state_methods[m.group(1)] = method

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
            )
            fn(seq, const, *args, **kwargs)
            return (seq, const)

        return wrapper_FSM

    @classmethod
    def get(cls, clk, rst, state_var, initial, edge="rise", lvl=1):
        """Get sequential block."""
        seq = ClockedBlock.get(clk, edge)
        const = []
        rst_if = HDLIfElse(rst == lvl, tag="rst_if")
        seq.add(rst_if)

        # add cases
        states = cls._collect_states()
        cases = []
        state_mapping = OrderedDict()

        # set state variable size
        state_var.set_size(int(math.ceil(math.log2(float(len(states))))))

        # add switch
        sw = HDLSwitch(state_var)
        rst_if.add_to_else_scope(sw)

        i = 0
        for state, method in states.items():
            state_mapping[state] = i
            case = HDLCase(
                HDLMacroValue(state), tag="__autogen_case_{}".format(state)
            )
            case.add_to_scope(
                HDLComment(
                    "case {}".format(state),
                    tag="__autogen_case_{}".format(state),
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
        return (seq, const)


class ParallelBlock:
    """Parallel scope."""

    def __init__(self, *args):
        """Initialize."""
        pass

    def __call__(self, fn):
        """Decorate."""

        @wraps(fn)
        def wrapper_ParallelBlock(*args, **kwargs):
            par = self.get()
            fn(par, *args, **kwargs)
            return par

        return wrapper_ParallelBlock

    @staticmethod
    def get():
        """Get a parallel scope."""
        return HDLScope(scope_type="par")
