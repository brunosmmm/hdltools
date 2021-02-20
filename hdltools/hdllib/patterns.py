"""Common HDL patterns."""

from ..abshdl.seq import HDLSequentialBlock
from ..abshdl.ifelse import HDLIfElse, HDLIfExp
from ..abshdl.sens import HDLSensitivityDescriptor, HDLSensitivityList
from ..abshdl.scope import HDLScope
from ..abshdl.module import HDLModule
from ..abshdl.port import HDLModulePort
from ..abshdl.switch import HDLSwitch, HDLCase
from ..abshdl.macro import HDLMacro, HDLMacroValue
from ..abshdl.assign import HDLAssignment
from ..abshdl.comment import HDLComment
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.signal import HDLSignal, HDLSignalSlice
from functools import wraps


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
    clock_signal,
    rst_signal,
    clk_edge,
    rst_lvl,
    rst_stmts,
    stmts=None,
    **kwargs
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

    def __init__(self, *args, **kwargs):
        """Initialize."""
        self.signals = args
        self._kwargs = kwargs

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

    def __init__(self, clk, edge="rise", *args, **kwargs):
        """Initialize."""
        super().__init__(clk, edge, *args, **kwargs)
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

    def __init__(self, clk, rst, clk_edge="rise", rst_lvl=1, **kwargs):
        """Initialize."""
        super().__init__(clk, clk_edge, rst, **kwargs)
        self.rst = rst
        self.lvl = rst_lvl
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


def get_multiplexer(target, select, *options):
    """Generate multiplexer pattern."""
    if len(options) < 2:
        raise RuntimeError("must have 2 or more options")
    for idx, opt in enumerate(options):
        if not isinstance(opt, (HDLSignal, HDLSignalSlice, HDLModulePort)):
            raise RuntimeError(
                "options must be signals or ports, got: {}".format(type(opt))
            )
        if isinstance(opt, HDLModulePort):
            opt = opt.signal.name
        # None is placeholder for last expression
        if idx < len(options) - 1:
            _ifexp = HDLIfExp(HDLExpression(select == idx), opt, None)
        if idx == 0:
            ifexp = _ifexp
            root_ifexp = _ifexp
        else:
            # update last expression
            if idx == len(options) - 1:
                ifexp.else_value = opt
            else:
                ifexp.else_value = _ifexp
                ifexp = _ifexp

    return HDLAssignment(target, root_ifexp)
