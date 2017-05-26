"""Common HDL patterns."""

from ..abshdl.seq import HDLSequentialBlock
from ..abshdl.ifelse import HDLIfElse
from ..abshdl.sens import HDLSensitivityDescriptor, HDLSensitivityList


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
    if rst_lvl == 0:
        rst_cmp = rst_signal == 0
    else:
        rst_cmp = rst_signal == 1
    ifelse = HDLIfElse(rst_cmp,
                       if_scope=rst_stmts,
                       else_scope=stmts)
    seq.add(ifelse)

    return seq
