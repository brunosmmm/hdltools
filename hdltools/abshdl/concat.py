"""Concatenation."""

from . import HDLObject
from .expr import HDLExpression
from .signal import HDLSignal, HDLSignalSlice
from .const import HDLIntegerConstant


class HDLConcatenation(HDLObject):
    """Concatenation of HDLObjects."""

    def __init__(self, *args):
        """Initialize."""
        self.items = []

        # HDLExpression is unconstrained!
        for arg in args:
            self.items.append(self._check_item(arg))

    def _check_item(self, item):
        if isinstance(item, HDLExpression):
            arg_expr = item
        elif isinstance(item, (HDLSignal, HDLSignalSlice,
                               HDLIntegerConstant, int)):
            arg_expr = HDLExpression(item)
        else:
            raise TypeError('Only types convertible to HDLExpression'
                            ' allowed, '
                            'not "{}"'.format(item.__class__.__name__))

        return arg_expr

    def __getitem__(self, _slice):
        pass

    def __delitem__(self, _slice):
        pass

    def __setitem__(self, _slice):
        pass

    def append(self, item):
        """Add item."""
        self.items.append(self._check_item(item))

    def __len__(self):
        """Get length."""
        total_length = 0
        for item in self.items:
            item_length = len(item)
            if item_length is None:
                raise ValueError('cannot determine total length')

            total_length += item_length

        return total_length
