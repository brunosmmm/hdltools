"""Testbench vector generation."""

from importlib.resources import files
from textx.metamodel import metamodel_from_file
from hdltools.vecgen.generate import VecgenPass

METAMODEL_FILE = str(files("hdltools") / "vecgen" / "vecgrammar.tx")

# Standard metamodel creation - comments will be handled by preprocessing
VECGEN_METAMODEL = metamodel_from_file(METAMODEL_FILE)


def parse_vecgen(text):
    """Parse vecgen file."""
    # Remove comments before parsing
    import re
    # Remove // style comments but preserve newlines
    text_no_comments = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
    
    # Recreate metamodel to pick up grammar changes
    mm = metamodel_from_file(METAMODEL_FILE)
    model = mm.model_from_str(text_no_comments)
    _pass = VecgenPass(text_no_comments)
    return _pass.visit(model)


def parse_vecgen_file(path):
    """Parse from file."""
    with open(path, "r") as vecf:
        contents = vecf.read()

    return parse_vecgen(contents)
