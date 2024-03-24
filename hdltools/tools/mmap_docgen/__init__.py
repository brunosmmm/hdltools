#!/usr/bin/env python3

"""Build documentation from memory mapped descriptions."""

import argparse
import os
import textx
from scoff.ast.visits import VisitError

from hdltools.mmap.builder import MMBuilder, MMBuilderSemanticError
from hdltools.mmap import parse_mmap_file
from hdltools.docgen.ghmd import GHMarkDownTable, GHMarkDownDocument
from hdltools.docgen.markdown import MarkDownHeader
from hdltools.tools.common.mmap import (
    add_param_replace_args,
    parse_param_replace_args,
    MmapError,
)
from hdltools.logging import DEFAULT_LOGGER

DEBUG = bool(os.environ.get("DEBUG", False))


def main():
    # argument parser
    arg_parser = argparse.ArgumentParser(
        description="Generate documentation"
        " from memory mapped interface"
        " description"
    )

    arg_parser.add_argument("model", help="Model file")
    arg_parser.add_argument("--output", help="Output file", action="store")
    arg_parser.add_argument(
        "-v", "--verbose", help="Verbose output", action="store_true"
    )
    add_param_replace_args(arg_parser)

    args = arg_parser.parse_args()

    if args.verbose:
        DEFAULT_LOGGER.set_level("debug")

    try:
        param_replacements = parse_param_replace_args(args)
    except MmapError as ex:
        DEFAULT_LOGGER.error(str(ex))
        if DEBUG:
            raise ex
        exit(1)

    try:
        text, mmap_model = parse_mmap_file(args.model)
    except textx.exceptions.TextXSyntaxError as ex:
        DEFAULT_LOGGER.error(f"syntax error: {ex}")
        if DEBUG:
            raise ex
        exit(1)
    mmbuilder = MMBuilder(text)
    try:
        mmap = mmbuilder.visit(mmap_model, param_replace=param_replacements)
    except VisitError as ex:
        embedded_ex = ex.find_embedded_exception()
        if isinstance(embedded_ex, MMBuilderSemanticError):
            DEFAULT_LOGGER.error(f"semantic error: {embedded_ex}")
            if DEBUG:
                raise ex
            exit(1)
        DEFAULT_LOGGER.error(f"unhandled exception: {embedded_ex}")
        if DEBUG:
            raise ex
        exit(1)
    doc = GHMarkDownDocument()

    # build documentation
    doc.append(MarkDownHeader("Memory Mapped Registers"), newline=True)
    reg_table = GHMarkDownTable(["Address", "Name", "Description"])

    for name, reg in mmap.registers.items():
        if "description" in reg.properties:
            descr = reg.properties["description"]
        else:
            descr = "---"
        reg_table.add_line(hex(reg.addr), name, descr)

    doc.append(reg_table)

    for name, reg in mmap.registers.items():
        if not reg.fields:
            # no fields, skip
            continue
        doc.append(
            MarkDownHeader("{} register details".format(name), level=2),
            newline=True,
        )

        reg_fields = GHMarkDownTable(
            ["Bits", "Name", "Access", "Description", "Reset Value"]
        )
        for field in reg.fields:
            descr = field.properties.get("description", "---")
            reset_val = field.default_value
            reset_val = hex(reset_val) if reset_val is not None else "?"
            reg_fields.add_line(
                field.dumps_slice(),
                field.name,
                field.permissions,
                descr,
                reset_val,
            )
        doc.append(reg_fields)

    if args.output is not None:
        with open(args.output, "w") as f:
            f.write(doc.dumps())

    else:
        print(doc)


if __name__ == "__main__":
    main()
