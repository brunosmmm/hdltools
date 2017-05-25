"""Test verilog codegen."""

from hdltools.abshdl.ifelse import HDLIfElse
from hdltools.abshdl.scope import HDLScope
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.signal import HDLSignal, HDLSignalSlice
from hdltools.abshdl.assign import HDLAssignment
from hdltools.abshdl.sens import HDLSensitivityList, HDLSensitivityDescriptor
from hdltools.abshdl.seq import HDLSequentialBlock
from hdltools.abshdl.module import HDLModule, HDLModulePort, HDLModuleParameter
from hdltools.abshdl.const import HDLIntegerConstant
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

def test_always():

    gen = VerilogCodeGenerator()

    sig = HDLSignal(sig_type='reg', sig_name='clk', size=1)
    sens = HDLSensitivityDescriptor(sens_type='rise', sig=sig)
    sens_list = HDLSensitivityList()
    sens_list.add(sens)

    test_sig = HDLSignal(sig_type='reg', sig_name='counter', size=2)
    rst_assign = HDLAssignment(signal=test_sig, value=0)
    norm_expr = HDLExpression(test_sig) + 1
    norm_assign = HDLAssignment(signal=test_sig, value=norm_expr)

    rst = HDLSignal(sig_type='reg', sig_name='rst', size=1)
    ifelse = HDLIfElse(condition=rst)
    ifelse.add_to_if_scope(rst_assign)
    ifelse.add_to_else_scope(norm_assign)

    seq = HDLSequentialBlock(sensitivity_list=sens_list)
    seq.add(ifelse)

    print(gen.dump_element(seq))

def test_module():

    gen = VerilogCodeGenerator()

    inp = HDLModulePort(direction='in', name='an_input', size=4)
    out = HDLModulePort(direction='out', name='an_output', size=1)
    prm = HDLModuleParameter(param_name='a_parameter',
                             param_type='integer',
                             param_default=HDLIntegerConstant(0))

    mod = HDLModule(module_name='my_module', ports=[inp, out],
                    params=[prm])

    print(gen.dump_element(mod))
