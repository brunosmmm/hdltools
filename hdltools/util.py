"""Utility functions."""

from math import ceil, log


def clog2(value):
    """Get clog2."""
    return int(ceil(log(value, 2))) + 1
