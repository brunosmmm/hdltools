from hdldraw.verilog import VerilogModuleParser
from hdldraw.hdl import (HDLVectorDescriptor,
                         HDLModulePort,
                         HDLModule,
                         HDLModuleParameter)
import os


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
    mod = HDLModule('my_module',
                    ports=[HDLModulePort('in',
                                         'myport',
                                         8)],
                    params=HDLModuleParameter('myparam',
                                              'integer',
                                              0))
    print(mod.dumps())

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

def test_verilog_parser():

    parser = VerilogModuleParser(os.path.join('tests',
                                              'assets',
                                              'verilog',
                                              'test.v'))
    model = parser.get_module()
