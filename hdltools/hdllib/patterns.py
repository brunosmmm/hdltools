"""Common HDL patterns."""

from ..abshdl.seq import HDLSequentialBlock
from ..abshdl.ifelse import HDLIfElse
from ..abshdl.sens import HDLSensitivityDescriptor, HDLSensitivityList
from ..abshdl.scope import HDLScope
from ..abshdl.module import HDLModule, HDLModulePort
from ..abshdl.switch import HDLSwitch, HDLCase
from ..abshdl.macro import HDLMacro
from ..abshdl.assign import HDLAssignment
from functools import wraps
from collections import OrderedDict
import inspect
import re


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


def get_clock_rst_block(clock_signal, rst_signal, clk_edge,
                        rst_lvl, rst_stmts, stmts=None, **kwargs):
    """Get a clocked block, with synchronous reset."""
    clk_sens = HDLSensitivityDescriptor(clk_edge, clock_signal)
    sens = HDLSensitivityList(clk_sens)
    seq = HDLSequentialBlock(sens, **kwargs)
    ifelse = get_reset_if_else(rst_signal, rst_lvl, rst_stmts, stmts, **kwargs)
    seq.add(ifelse)

    return seq


def get_any_sequential_block(*stmts, **kwargs):
    """Get a block that is sensitive to anything."""
    any_sens = HDLSensitivityDescriptor('any')
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
    ifelse = HDLIfElse(rst_cmp,
                       if_scope=rst_stmts,
                       else_scope=stmts)

    return ifelse


def get_module(name, inputs=None, outputs=None):
    """Get a module."""
    module_ports = []
    for inp in inputs:
        module_ports.append(HDLModulePort('in', *inp))
    for out in outputs:
        module_ports.append(HDLModulePort('out', *out))

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
                sens_descrs.append(HDLSensitivityDescriptor('rise', arg))
            sens_list = HDLSensitivityList(*sens_descrs)
        seq = HDLSequentialBlock(sens_list)
        return seq


class ClockedBlock(SequentialBlock):
    """Clocked sequential block."""

    def __init__(self, clk, edge='rise'):
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
    def get(clk, edge='rise'):
        """Get Clocked block."""
        sens_list = HDLSensitivityList(HDLSensitivityDescriptor(edge,
                                                                clk))
        seq = HDLSequentialBlock(sens_list)
        return seq


class ClockedRstBlock(ClockedBlock):
    """Clocked sequential block with reset."""

    def __init__(self, clk, rst, clk_edge='rise', rst_lvl=1):
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
    def get(clk, rst, edge='rise', lvl=1):
        """Get sequential block."""
        seq = ClockedBlock.get(clk, edge)
        rst_if = HDLIfElse(rst == lvl, tag='rst_if')
        seq.add(rst_if)
        return seq


class FSM(ClockedBlock):
    """Finite state machine."""

    def __init__(self, clk, rst, state_var,
                 initial, clk_edge='rise', rst_lvl=1):
        """Initialize."""
        super().__init__(clk, rst, clk_edge, rst_lvl)
        self.initial = initial
        self.state_var = state_var

    @classmethod
    def _collect_states(cls):
        state_methods = {}
        for method_name, method in inspect.getmembers(cls):
            cls_name = cls.__name__
            m = re.match(r'_{}__state_([a-zA-Z0-9_]+)'.format(cls_name),
                         method_name)
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
            seq, const = self.get(self.clk, self.rst, self.state_var,
                                  self.initial, self.edge, self.lvl)
            fn(seq, const, *args, **kwargs)
            return seq
        return wrapper_FSM

    @classmethod
    def get(cls, clk, rst, state_var, initial, edge='rise', lvl=1):
        """Get sequential block."""
        seq = ClockedBlock.get(clk, edge)
        const = []
        rst_if = HDLIfElse(rst == lvl, tag='rst_if')
        seq.add(rst_if)

        # add switch
        sw = HDLSwitch(state_var)
        rst_if.add_to_else_scope(sw)

        # add cases
        states = cls._collect_states()
        cases = []
        state_mapping = OrderedDict()

        i = 0
        for state, method in states.items():
            state_mapping[state] = i
            case = HDLCase(i)
            cases.append(case)
            sw.add_case(case)
            const.append(HDLMacro(state, i))
            i += 1

        if initial in state_mapping:
            rst_if.add_to_if_scope(HDLAssignment(state_var,
                                                 state_mapping[initial]))
        else:
            print(initial)
            raise IOError('askdjakdjaskdjadksadkj')

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
        return HDLScope(scope_type='par')
