from hdltools.verilog.parser import (VerilogModuleParser,
                                     verilog_bitstring_to_int)
from hdltools.abshdl.vector import HDLVectorDescriptor
from hdltools.abshdl.module import (HDLModulePort,
                                    HDLModule,
                                    HDLModuleParameter)
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.signal import HDLSignal, HDLSignalSlice
from hdltools.abshdl.const import HDLIntegerConstant
from hdltools.abshdl.sens import HDLSensitivityList, HDLSensitivityDescriptor
from hdltools.abshdl.seq import HDLSequentialBlock
from hdltools.abshdl.assign import HDLAssignment
import os
import ast

def test_constants():

    fit = HDLIntegerConstant.value_fits_width(8, 256)
    if fit is True:
        raise Exception
    fit = HDLIntegerConstant.value_fits_width(8, 255)
    if fit is False:
        raise Exception

# test HDL primitives
def test_vector_descriptor():

    # basic testing
    vec = HDLVectorDescriptor(0, 0)
    print(vec.dumps())
    if len(vec) != 1:
        raise Exception

    vec = HDLVectorDescriptor(7)

    # test failure modes
    try:
        vec = HDLVectorDescriptor(-1, 0)
        raise Exception
    except ValueError:
        pass

    try:
        vec = HDLVectorDescriptor('1', 0)
        raise Exception
    except TypeError:
        pass

    try:
        vec = HDLVectorDescriptor(left_size=1, right_size='1')
        raise Exception
    except TypeError:
        pass

    try:
        vec = HDLVectorDescriptor(7, stored_value='a')
        raise Exception
    except TypeError:
        pass

    vec = HDLVectorDescriptor(8, stored_value=256)
    left, right = vec.evaluate()

    try:
        HDLVectorDescriptor(7, stored_value=256)
        raise Exception
    except ValueError:
        pass

def test_module_port():

    port = HDLModulePort('in', 'myport', 3)
    port = HDLModulePort('out', 'myport', (2, 0))
    port = HDLModulePort('inout', 'myport', HDLVectorDescriptor(2, 0))
    print(port.dumps())

    # fail cases
    try:
        port = HDLModulePort('unknown', 'myport', 0)
        raise Exception
    except ValueError:
        pass

    try:
        port = HDLModulePort('in', 'myport', -1)
        raise Exception
    except ValueError:
        pass

    try:
        port = HDLModulePort('in', 'myport', (2, 3, 0))
        raise Exception
    except ValueError:
        pass

    try:
        port = HDLModulePort('in', 'myport', 'INVALID')
        raise Exception
    except TypeError:
        pass

def test_hdl_parameter():

    param = HDLModuleParameter('myparam', 'integer', param_default=0)
    print(param.dumps())

def test_hdl_module():

    mod = HDLModule('my_module')
    mod = HDLModule('my_module', [HDLModulePort('in', 'myport', 8)])
    mod = HDLModule('my_module', params=[HDLModuleParameter('myparam',
                                                            'integer',
                                                            0)])

    expr = ast.parse('myparam-1', mode='eval')
    vec = HDLVectorDescriptor(left_size=HDLExpression(expr),
                              right_size=0)
    mod = HDLModule('my_module',
                    ports=[HDLModulePort('in',
                                         'myport',
                                         vec)],
                    params=HDLModuleParameter('myparam',
                                              'integer',
                                              0))
    print(mod.dumps(evaluate=True))

    param_scope = mod.get_parameter_scope()
    full_scope = mod.get_full_scope()
    params = mod.get_param_names()
    ports = mod.get_port_names()

    # failures
    try:
        mod = HDLModule('my_module', 0)
        raise Exception
    except TypeError:
        pass

    try:
        mod = HDLModule('my_module', [0])
        raise Exception
    except TypeError:
        pass

    try:
        mod = HDLModule('my_module', params=[0])
        raise Exception
    except TypeError:
        pass

    try:
        mod = HDLModule('my_module', params=0)
        raise Exception
    except TypeError:
        pass

def test_hdl_expression():

    expr_1 = 'PARAM-2'
    expr_2 = 'PARAM_X+1'
    hdl_expr_1 = HDLExpression(ast.parse(expr_1, mode='eval'))
    hdl_expr_2 = HDLExpression(ast.parse(expr_2, mode='eval'))
    sum = hdl_expr_1 + hdl_expr_2
    print(sum.dumps())

    my_signal = HDLSignal('reg', 'signal_a', size=2)
    _ = HDLExpression(HDLIntegerConstant(1))
    _ = HDLExpression(1)
    _ = HDLExpression(my_signal)
    _ = HDLExpression(HDLSignalSlice(my_signal, 1))
    _ = HDLExpression(my_signal[1:0])

def test_hdl_signal():

    my_sig = HDLSignal('reg', 'signal_x', size=(7, 0))
    print(my_sig.dumps())
    my_sliced_sig = my_sig[3:1]
    other_slice = my_sig[7]
    yet_another = my_sig[2:]
    another = my_sig[:2]
    print(yet_another.dumps())
    _ = HDLSignal('reg', 'sig', HDLVectorDescriptor(1, 0))

    # exceptions
    try:
        _ = HDLSignal('unknown', 'sig', 1)
        raise Exception
    except ValueError:
        pass

    try:
        _ = HDLSignal('reg', 'sig', -1)
        raise Exception
    except ValueError:
        pass

    try:
        _ = HDLSignal('reg', 'sig', (1, 2, 3))
        raise Exception
    except ValueError:
        pass

    try:
        _ = HDLSignal('reg', 'sig', 'invalid')
        raise Exception
    except TypeError:
        pass

    _ = HDLSignalSlice(my_sig, HDLVectorDescriptor(1, 0))

    try:
        _ = HDLSignalSlice(my_sig, 'invalid')
        raise Exception
    except TypeError:
        pass

def test_sens():

    some_signal = HDLSignal('reg', 'signal', size=1)
    sens_1 = HDLSensitivityDescriptor(sens_type='rise', sig=some_signal)

    sens_list = HDLSensitivityList()
    sens_list.add(sens_1)

    print(sens_list.dumps())

def test_seq():

    some_signal = HDLSignal('reg', 'signal', size=1)
    sens_1 = HDLSensitivityDescriptor(sens_type='rise', sig=some_signal)

    sens_list = HDLSensitivityList()
    sens_list.add(sens_1)

    ass_sig = HDLSignal('reg', 'counter', size=2)
    ass_expr = HDLExpression(ass_sig) + 1
    assign = HDLAssignment(ass_sig, ass_expr)

    seq = HDLSequentialBlock(sens_list)
    seq.add(assign)

    print(seq.dumps())

def test_assign():

    # this module is extensively tested already, being used as a support
    # class for many others. here we test whatever is missing

    sig = HDLSignal('comb', 'my_signal')
    assign = HDLAssignment(signal=sig, value=0)
    print(assign.dumps())

    # test fail cases
    try:
        _ = HDLAssignment('not_allowed', 0)
        raise Exception
    except TypeError:
        pass
