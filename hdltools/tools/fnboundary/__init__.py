#!/usr/bin/env python3
"""Determine function boundaries."""

from argparse import ArgumentParser
from hdltools.binutils.passes import AsmDumpPass
from hdltools.binutils import parse_objdump
from hdltools.binutils.tools.boundary import get_boundaries


def main():
    parser = ArgumentParser()
    parser.add_argument("asm", help="output from objdump")
    exclusive = parser.add_mutually_exclusive_group()
    exclusive.add_argument(
        "--list-fns", help="list functions", action="store_true"
    )
    exclusive.add_argument("--fn-boundary", help="get function boundary")

    args = parser.parse_args()

    with open(args.asm, "r") as asmdump:
        dumpcontents = asmdump.read()

    dump_pass = AsmDumpPass()
    dump_pass.visit(parse_objdump(dumpcontents))

    if args.list_fns:
        for fn in dump_pass.get_functions():
            print(fn)
    elif args.fn_boundary is not None:
        for name, fn in dump_pass.get_functions().items():
            if name == args.fn_boundary:
                print("{}, {}".format(*get_boundaries(fn)))
                exit(0)

        print(f"ERROR: function {args.fn_boundary} not found")
        exit(1)


if __name__ == "__main__":
    main()
