"""Utility functions."""

from ..abshdl.concat import HDLConcatenation


def concat(*args):
    """Concatenate."""
    return HDLConcatenation(*args, direction="lr")
