#!/bin/python

"""Build AXI MM Slaves from specification files."""
import argparse
import os
from hdltools.abshdl.mmap import MemoryMappedInterface
from hdltools.abshdl.macro import HDLMacro
from hdltools.abshdl.signal import HDLSignal
from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.template import HDLTemplateParser
from hdltools.abshdl.const import HDLIntegerConstant
from hdltools.abshdl.assign import HDLAssignment
from hdltools.abshdl.module import HDLModuleParameter


DEFAULT_TEMPLATE = os.path.join('assets', 'verilog', 'axi_slave.v')

if __name__ == "__main__":

    # argument parser
    arg_parser = argparse.ArgumentParser(description='Build AXI MM'
                                         ' Slaves from high-level description')

    arg_parser.add_argument('model', help='Model file')
    arg_parser.add_argument('--template', help='Template file', action='store')

    args = arg_parser.parse_args()

    # the memory mapped interface descriptor
    mmap = MemoryMappedInterface()

    # parse file
    mmap.parse_file(args.model)

    print(mmap.dumps())

    # code generator
    vlog = VerilogCodeGenerator()
    vlog.add_class_alias('HDLModulePort', 'FlagPort')

    # get template and populate
    tmp = HDLTemplateParser()
    tmp.parse_file(DEFAULT_TEMPLATE)

    # parameters (naive implementation)
    param_loc = tmp.find_template_tag('USER_PARAMS')
    if param_loc is None:
        raise ValueError('invalid template file')

    param_list = ['/* USER PARAMETERS */']
    for name, value in mmap.parameters.items():
        param = HDLModuleParameter(name, None, param_default=value)
        param_list.append(vlog.dump_element(param))

    tmp.insert_contents(param_loc, '\n'.join(param_list))

    # bit field declarations
    bits_loc = tmp.find_template_tag('REGISTER_BITS')
    if bits_loc is None:
        raise ValueError('invalid template file')

    # prepare contents and insert
    define_list = ['/* REGISTER BIT FIELD DEFINITIONS */']
    for name, reg in mmap.registers.items():
        for field in reg.fields:
            def_name = '{}_{}_INDEX'.format(name, field.name)
            def_value = field.get_range()[0]
            macro = HDLMacro(def_name, def_value)
            define_list.append(vlog.dump_element(macro))

    tmp.insert_contents(bits_loc, '\n'.join(define_list))

    # ports
    port_loc = tmp.find_template_tag('USER_PORTS')
    if port_loc is None:
        raise ValueError('invalid template file')

    port_list = ['/* FIELD DEPENDENT PORTS */']
    for name, port in mmap.ports.items():
        port_list.append(vlog.dump_element(port))
    tmp.insert_contents(port_loc, '\n'.join(port_list))

    # registers
    reg_signal_loc = tmp.find_template_tag('REGISTER_DECL')
    if reg_signal_loc is None:
        raise ValueError('invalid template file')

    reg_decl_list = ['/* REGISTERS */']
    for name, reg in mmap.registers.items():
        signal = HDLSignal('reg', 'REG_'+name, reg.size)
        reg_decl_list.append(vlog.dump_element(signal))
    tmp.insert_contents(reg_signal_loc, '\n'.join(reg_decl_list))

    # register reset value
    reg_reset_loc = tmp.find_template_tag('LOGIC_RESET')
    if reg_reset_loc is None:
        raise ValueError('invalid template file')

    reg_reset_list = ['/* RESET REGISTERS */']
    for name, reg in mmap.registers.items():
        signal = HDLSignal('reg', 'REG_'+name, reg.size)
        value = reg.get_default_value()
        def_val = HDLIntegerConstant(value, size=reg.size)
        assignment = HDLAssignment(signal, def_val)
        reg_reset_list.append(vlog.dump_element(assignment))
    tmp.insert_contents(reg_reset_loc, '\n'.join(reg_reset_list))

    # output port assignments
    assign_logic_loc = tmp.find_template_tag('ASSIGN_LOGIC')
    if assign_logic_loc is None:
        raise ValueError('invalid template file')

    assign_list = ['/* OUTPUT FLAG ASSIGNMENTS */']
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
        assign_list.append(vlog.dump_element(assignment))
    tmp.insert_contents(assign_logic_loc, '\n'.join(assign_list))

    print(tmp._dumps_templated())
