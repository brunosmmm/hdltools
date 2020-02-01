"""Test vector generation."""

import os
from hdltools.vecgen import parse_vecgen_file


def test_vecgen():
    """Test input vector generation."""

    cwd = os.getcwd()
    ret = parse_vecgen_file(os.path.join(cwd, "assets/tests/input1.vg"))
