#!/bin/python

"""Build AXI MM Slaves from specification files."""
import argparse
import os
from hdltools.mmap import MemoryMappedInterface
from hdltools.verilog.codegen import dumps_define, dumps_vector
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

    # get template and populate
    tmp = HDLTemplateParser()
    tmp.parse_file(DEFAULT_TEMPLATE)

    bits_loc = tmp.find_template_tag('REGISTER_BITS')
    if bits_loc is None:
        raise ValueError('invalid template file')

    # prepare contents and insert
    define_list = []
    for name, reg in mmap.registers.items():
        for field in reg.fields:
            def_name = '{}_{}_INDEX'.format(name, field.name)
            def_value = field.get_range()[0]
            define_list.append(dumps_define(def_name, def_value))

    tmp.insert_contents(bits_loc, '\n'.join(define_list))

    #print(tmp._dumps_templated())
