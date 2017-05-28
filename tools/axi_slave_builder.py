#!/bin/python

"""Build AXI MM Slaves from specification files."""
import argparse
import os
from hdltools.abshdl.mmap import MemoryMappedInterface
from hdltools.abshdl.macro import HDLMacro
from hdltools.abshdl.signal import HDLSignal
from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.abshdl.const import HDLIntegerConstant
from hdltools.abshdl.assign import HDLAssignment
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.concat import HDLConcatenation
from hdltools.hdllib.aximm import get_axi_mm_slave


DEFAULT_TEMPLATE = os.path.join('assets', 'verilog', 'axi_slave.v')

if __name__ == "__main__":

    # argument parser
    arg_parser = argparse.ArgumentParser(description='Build AXI MM'
                                         ' Slaves from high-level description')

    arg_parser.add_argument('model', help='Model file')
    arg_parser.add_argument('--template', help='Template file', action='store')
    arg_parser.add_argument('--modname', help='Module name',
                            default='aximm_slave', action='store')

    args = arg_parser.parse_args()

    # the memory mapped interface descriptor
    mmap = MemoryMappedInterface()

    # parse file
    mmap.parse_file(args.model)

    print(mmap.dumps())

    # code generator
    vlog = VerilogCodeGenerator(indent=True)
    vlog.add_class_alias('HDLModulePort', 'FlagPort')

    slave = get_axi_mm_slave(args.modname,
                             mmap.reg_size,
                             len(mmap.get_register_list()))

    # parameters (naive implementation)
    for name, value in mmap.parameters.items():
        slave.add_parameters(value)

    # bit field declarations
    for name, reg in mmap.registers.items():
        for field in reg.fields:
            def_name = '{}_{}_INDEX'.format(name, field.name)
            def_value = field.get_range()[0]
            macro = HDLMacro(def_name, def_value)
            slave.add_constants(macro)

    for name, port in mmap.ports.items():
        slave.add_ports(port)

    for name, reg in mmap.registers.items():
        signal = HDLSignal('reg', 'REG_'+name, reg.size)
        # TODO: fixme: allow only to insert list, because
        # signal will be iterated and bad things will happen
        slave.insert_after('REG_DECL', [signal])

    param_buffer_list = []
    for name, reg in mmap.registers.items():
        signal = HDLSignal('reg', 'REG_'+name, reg.size)
        value = reg.get_default_value()
        if isinstance(value, (HDLIntegerConstant, int)):
            def_val = HDLIntegerConstant(value, size=reg.size)
        elif isinstance(value, HDLExpression):
            raise TypeError('HDLExpression not implemented at this time')
        elif isinstance(value, HDLConcatenation):
            def_val = value

            concat = HDLConcatenation()
            # build parameter buffers
            for field in reg.fields:
                if isinstance(field.default_value, HDLExpression):
                    param_name = field.default_value.dumps()
                    if param_name in mmap.parameters:
                        sig = HDLSignal('const',
                                        'PRM_'+param_name,
                                        size=len(field.default_value),
                                        default_val=param_name)
                        slave.insert_before('USER_LOGIC', [sig])
                        new_expr = HDLExpression('PRM_'+param_name,
                                                 size=len(field.default_value))
                        concat.append(new_expr)
                else:
                    concat.append(field.default_value)

            def_val = concat
        else:
            raise TypeError('Invalid type')

        slave.insert_after('REG_RESET', [signal.assign(def_val)])

    for name, port in mmap.ports.items():
        if port.direction != 'out':
            continue
        # create a proxy signal
        sig = HDLSignal('comb', name, port.vector)
        reg_sig = HDLSignal('reg', 'REG_'+port.target_register.name,
                            port.target_register.size)
        target_field = port.target_register.get_field(port.target_field)
        target_bits = target_field.get_slice()
        assignment = HDLAssignment(sig, reg_sig[target_bits])
        slave.insert_after('OUTPUT_ASSIGN', [assignment])

    print(vlog.dump_element(slave))
