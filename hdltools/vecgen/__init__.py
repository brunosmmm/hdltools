"""Testbench vector generation."""

import pkg_resources
from textx.metamodel import metamodel_from_file
from hdltools.vecgen.generate import VecgenPass

METAMODEL_FILE = pkg_resources.resource_filename(
    "hdltools", "vecgen/vecgrammar.tx"
)
VECGEN_METAMODEL = metamodel_from_file(METAMODEL_FILE)


def parse_vecgen(text):
    """Parse vecgen file."""
    model = VECGEN_METAMODEL.model_from_str(text)
    _pass = VecgenPass(text)
    return _pass.visit(model)


def parse_vecgen_file(path):
    """Parse from file."""
    with open(path, "r") as vecf:
        contents = vecf.read()

    return parse_vecgen(contents)
