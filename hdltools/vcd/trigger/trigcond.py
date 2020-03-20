"""Trigger condition mini-language."""

import pkg_resources
from textx.metamodel import metamodel_from_file

METAMODEL_FILE = pkg_resources.resource_filename(
    "hdltools", "vcd/trigger/trigcond.tx"
)
OBJDUMP_METAMODEL = metamodel_from_file(METAMODEL_FILE)


def parse_trigcond(text):
    """Parse vecgen file."""
    model = OBJDUMP_METAMODEL.model_from_str(text)
    return model
