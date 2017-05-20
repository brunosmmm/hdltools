#!/bin/python

"""Build AXI MM Slaves from specification files."""
import argparse
import os
from hdltools.abshdl.mmap import MemoryMappedInterface
from hdltools.abshdl.macro import HDLMacro
from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.template import HDLTemplateParser


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

    for name, reg in mmap.registers.items():
        pass

    print(tmp._dumps_templated())
