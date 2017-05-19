from hdltools.verilog.parser import (VerilogModuleParser,
                                     verilog_bitstring_to_int)
from hdltools.hdl import (HDLVectorDescriptor,
                          HDLModulePort,
                          HDLModule,
                          HDLModuleParameter,
                          HDLExpression)
import os
import ast

def test_hdl_primitives():

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
        vec = HDLVectorDescriptor(7, stored_value='a')
        raise Exception
    except TypeError:
        pass

    fit = HDLVectorDescriptor.value_fits_width(8, 256)
    if fit is True:
        raise Exception
    fit = HDLVectorDescriptor.value_fits_width(8, 255)
    if fit is False:
        raise Exception

    try:
        HDLVectorDescriptor(7, stored_value=256)
        raise Exception
    except ValueError:
        pass

    # ports
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

    # HDL Parameter
    param = HDLModuleParameter('myparam', 'integer', param_default=0)
    print(param.dumps())

    # HDL MODULE
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

    expr_1 = 'PARAM-2'
    expr_2 = 'PARAM_X+1'
    hdl_expr_1 = HDLExpression(ast.parse(expr_1, mode='eval'))
    hdl_expr_2 = HDLExpression(ast.parse(expr_2, mode='eval'))
    sum = hdl_expr_1 + hdl_expr_2
    print(sum.dumps())
    # raise

def test_verilog_parser():

    # bitstrings
    width, value = verilog_bitstring_to_int("4'b0011")
    print('{}, {}'.format(width, value))

    parser = VerilogModuleParser(os.path.join('assets',
                                              'verilog',
                                              'test.v'))
    model = parser.get_module()
