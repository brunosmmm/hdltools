"""Memory mapped interface description parser."""

import pkg_resources
from textx.metamodel import metamodel_from_file
from hdltools.abshdl.port import HDLModulePort
from hdltools.mmap.ast import MMAP_AST_CLASSES

MMAP_COMPILER_GRAMMAR = pkg_resources.resource_filename(
    "hdltools", "mmap/mmap.tx"
)

MMAP_METAMODEL = metamodel_from_file(
    MMAP_COMPILER_GRAMMAR, classes=MMAP_AST_CLASSES
)


def bitfield_pos_to_slice(pos):
    """Convert to slice from parser object."""
    ret = [int(pos.left)]
    if pos.right is not None:
        ret.append(int(pos.right))

    return ret


def slice_size(slic):
    """Get slice size in bits."""
    if len(slic) > 1:
        return slic[0] - slic[1] + 1
    else:
        return 1


class FlagPort(HDLModulePort):
    """A port dependent on a register field."""

    def __init__(self, target_register, target_field, direction, name):
        """Initialize."""
        if target_field is not None:
            field = target_register.get_field(target_field)
            field_size = len(field.get_range())
        else:
            field_size = target_register.size
        self.target_register = target_register
        self.target_field = target_field
        super().__init__(direction, name, field_size)


def parse_mmap_str(text):
    """Parse mmap definition."""
    return MMAP_METAMODEL.model_from_str(text)


def parse_mmap_file(fpath):
    """Parse file."""
    with open(fpath, "r") as f:
        text = f.read()

    ret = parse_mmap_str(text)

    return (text, ret)
