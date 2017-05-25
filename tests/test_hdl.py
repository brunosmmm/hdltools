from hdltools.verilog.parser import (VerilogModuleParser,
                                     verilog_bitstring_to_int)
from hdltools.abshdl.vector import HDLVectorDescriptor
from hdltools.abshdl.module import (HDLModulePort,
                                    HDLModule,
                                    HDLModuleParameter)
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.signal import HDLSignal, HDLSignalSlice
from hdltools.abshdl.const import (HDLIntegerConstant, HDLStringConstant)
from hdltools.abshdl.sens import HDLSensitivityList, HDLSensitivityDescriptor
from hdltools.abshdl.seq import HDLSequentialBlock
from hdltools.abshdl.assign import HDLAssignment
from hdltools.abshdl.concat import HDLConcatenation
import os
import ast

def test_constants():

    try:
        fit_1 = HDLIntegerConstant(256, size=8)
        raise Exception
    except ValueError:
        pass

    fit_1 = HDLIntegerConstant(255, size=8)
    fit_2 = HDLIntegerConstant(128, size=9)

    ret = 3 - fit_1
    ret = fit_1 - fit_2
    ret = fit_2 - fit_1
    ret = fit_1 + fit_2
    ret = 2 + fit_1
    ret = 2*fit_1
    ret = fit_1*2

    try:
        _ = HDLIntegerConstant(2) - '123'
        raise Exception
    except TypeError:
        pass

    try:
        _ = HDLIntegerConstant(2) + '123'
        raise Exception
    except TypeError:
        pass

    try:
        _ = HDLIntegerConstant(2)*1.0
        raise Exception
    except TypeError:
        pass

    ret = HDLIntegerConstant(2) == 2
    if ret is False:
        raise Exception

    try:
        _ = HDLIntegerConstant(2) == 'x'
        raise Exception
    except TypeError:
        pass

    x = abs(HDLIntegerConstant(-1))

    s = HDLStringConstant(value='some_value')
    print(s.dumps())

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
    print('*TEST_EXPR*')
    expr_1 = 'PARAM-2'
    expr_2 = 'PARAM_X+1'
    expr_3 = 'a and ~b'
    hdl_expr_1 = HDLExpression(ast.parse(expr_1, mode='eval'))
    hdl_expr_2 = HDLExpression(ast.parse(expr_2, mode='eval'))
    hdl_expr_3 = HDLExpression(expr_3)
    print(hdl_expr_3.dumps())
    sum = hdl_expr_1 + hdl_expr_2
    neg = ~sum
    bool_neg = sum.bool_neg()
    bool_and = hdl_expr_1.bool_and(hdl_expr_2)
    bool_or = hdl_expr_1.bool_or(hdl_expr_2)
    print(sum.dumps())
    print(neg.dumps())
    print(bool_neg.dumps())
    print(bool_and.dumps())
    print(bool_or.dumps())

    _ = hdl_expr_1 & 0x1
    _ = 0x1 | hdl_expr_1
    _ = 0x1 & hdl_expr_1
    _ = 0x1 ^ hdl_expr_1
    _ = hdl_expr_1 ^ 0x1

    my_signal = HDLSignal('reg', 'signal_a', size=2)
    _ = HDLExpression(HDLIntegerConstant(1))
    _ = HDLExpression(1)
    _ = HDLExpression(my_signal)
    _ = HDLExpression(HDLSignalSlice(my_signal, 1))
    _ = HDLExpression(my_signal[1:0])

    # test reduction
    expr_a = HDLExpression('value_a')
    expr_b = HDLExpression('value_b')
    full_expr = expr_a<<0 | expr_b<<16 | HDLExpression(0)

    case_1 = ast.BinOp(left=ast.Num(n=0),
                       op=ast.BitOr(),
                       right=ast.Name(id='VAR'))

    case_2 = ast.BinOp(left=ast.Num(n=1),
                       op=ast.Mult(),
                       right=ast.Name(id='VAR'))

    case_3 = ast.BinOp(left=ast.Num(n=0),
                       op=ast.Mult(),
                       right=ast.Name(id='VAR'))

    hdl_expr = HDLExpression(ast.Expression(body=case_1))
    hdl_expr_2 = HDLExpression(ast.Expression(body=case_2))
    hdl_expr_3 = HDLExpression(ast.Expression(body=case_3))
    print(hdl_expr.dumps())
    print(hdl_expr_2.dumps())

    reduced_1 = HDLExpression._reduce_binop(case_1)
    hdl_expr = HDLExpression(ast.Expression(body=reduced_1))
    print(hdl_expr.dumps())

    reduced_2 = HDLExpression._reduce_binop(case_2)
    hdl_expr_2 = HDLExpression(ast.Expression(body=reduced_2))
    print(hdl_expr_2.dumps())

    reduced_3 = HDLExpression._reduce_binop(case_3)
    hdl_expr_3 = HDLExpression(ast.Expression(body=reduced_3))
    print(hdl_expr_3.dumps())

    print(full_expr.dumps())
    full_expr.reduce_expr()
    print(full_expr.dumps())

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

def test_concat():
    print('*TEST CONCAT*')
    sig = HDLSignal('comb', 'my_signal', size=4)
    concat = HDLConcatenation(sig, HDLExpression(0x0c, size=8))
    if len(concat) != 12:
        raise ValueError

    concat.append(HDLExpression(0x1, size=1))

    # failures
    try:
        _ = HDLConcatenation(sig, 'not_allowed')
        raise Exception
    except TypeError:
        pass
