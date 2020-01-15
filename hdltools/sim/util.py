"""Utility functions."""

from ..abshdl.concat import HDLConcatenation
from ..hdllib.patterns import SequentialBlock

# globals
_block_count = 0


def concat(value, *args):
    """Concatenate."""
    return HDLConcatenation(value, *args, direction="lr")


def rising_edge(signal):
    """Rising edge."""
    global _block_count

    @SequentialBlock()
    def gen_block():
        # bla bla
        pass

    gen_block.__name__ = f"gen_{_block_count}"
    _block_count += 1

    return gen_block
