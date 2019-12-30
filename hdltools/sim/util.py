"""Utility functions."""

from ..abshdl.concat import HDLConcatenation


def concat(value, *args):
    """Concatenate."""
    return HDLConcatenation(value, *args, direction="lr")
