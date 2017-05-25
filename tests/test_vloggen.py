"""Test verilog codegen."""

from hdltools.abshdl.ifelse import HDLIfElse
from hdltools.abshdl.scope import HDLScope
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.signal import HDLSignal, HDLSignalSlice
from hdltools.abshdl.assign import HDLAssignment
from hdltools.verilog.codegen import VerilogCodeGenerator

def test_ifelse():

    # create an if-else block
    gen = VerilogCodeGenerator()

    sig = HDLSignal(sig_type='comb', sig_name='test', size=1)
    test_sig = HDLSignal(sig_type='reg', sig_name='counter', size=2)

    assign_rhs = HDLExpression(test_sig) + 1
    assignment = HDLAssignment(signal=test_sig, value=assign_rhs)

    ifelse = HDLIfElse(condition=sig)
    ifelse.add_to_if_scope(assignment)

    # make else
    assignment = HDLAssignment(signal=test_sig, value=0)
    ifelse.add_to_else_scope(assignment)

    print(gen.dump_element(ifelse))
