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
