#!/usr/bin/env python3

"""Build documentation from memory mapped descriptions."""

import argparse
import logging
import textx
from rich.logging import RichHandler
from rich.console import Console

from hdltools.mmap.builder import MMBuilder
from hdltools.mmap import parse_mmap_file
from hdltools.docgen.ghmd import GHMarkDownTable, GHMarkDownDocument
from hdltools.docgen.markdown import MarkDownHeader
from hdltools.tools.common.mmap import (
    add_param_replace_args,
    parse_param_replace_args,
    MmapError,
)

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(console=Console(stderr=True))],
)

logger = logging.getLogger("hdltools.mmap_docgen")


def main():
    # argument parser
    arg_parser = argparse.ArgumentParser(
        description="Generate documentation"
        " from memory mapped interface"
        " description"
    )

    arg_parser.add_argument("model", help="Model file")
    arg_parser.add_argument("--output", help="Output file", action="store")
    add_param_replace_args(arg_parser)

    args = arg_parser.parse_args()

    try:
        param_replacements = parse_param_replace_args(args)
    except MmapError as ex:
        logger.error(str(ex))
        exit(1)

    _, mmap = parse_mmap_file(args.model)
    try:
        text, mmap_model = parse_mmap_file(args.model)
    except textx.exceptions.TextXSyntaxError as ex:
        logger.error(f"syntax error: {ex}")
        exit(1)
    mmbuilder = MMBuilder(text)
    mmap = mmbuilder.visit(mmap_model, param_replace=param_replacements)
    doc = GHMarkDownDocument()

    # build documentation
    doc.append(MarkDownHeader("Memory Mapped Registers"), newline=True)
    reg_table = GHMarkDownTable(["Address", "Name", "Description"])

    for name, reg in mmap.registers.items():
        if "description" in reg.properties:
            descr = reg.properties["description"]
        else:
            descr = "---"
        reg_table.add_line(reg.addr, name, descr)

    doc.append(reg_table)

    for name, reg in mmap.registers.items():
        doc.append(
            MarkDownHeader("{} register details".format(name), level=2),
            newline=True,
        )

        reg_fields = GHMarkDownTable(["Bits", "Name", "Access", "Description"])
        for field in reg.fields:
            if "description" in field.properties:
                descr = field.properties["description"]
            else:
                descr = "---"
            reg_fields.add_line(
                field.dumps_slice(), field.name, field.permissions, descr
            )
        doc.append(reg_fields)

    if args.output is not None:
        with open(args.output, "w") as f:
            f.write(doc.dumps())

    else:
        print(doc)


if __name__ == "__main__":
    main()
