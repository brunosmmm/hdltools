"""Binary analysis utilities."""

from importlib.resources import files
from textx.metamodel import metamodel_from_file

METAMODEL_FILE = str(files("hdltools") / "binutils" / "objdump.tx")
OBJDUMP_METAMODEL = metamodel_from_file(METAMODEL_FILE)


def parse_objdump(text):
    """Parse vecgen file."""
    model = OBJDUMP_METAMODEL.model_from_str(text)
    return model


def parse_objdump_file(path):
    """Parse from file."""
    with open(path, "r") as vecf:
        contents = vecf.read()

    return parse_objdump(contents)


class AsmObject:
    """Assembly representation object."""
