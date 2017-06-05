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

    def append(self, item):
        """Add item."""
        self.items.append(self._check_item(item))

    def appendleft(self, item):
        """Add item on the left side."""
        _item = [self._check_item(item)]
        _item.extend(self.items)
        self.items = _item

    def __len__(self):
        """Get length."""
        total_length = 0
        for item in self.items:
            total_length += len(item)

        return total_length

    def dumps(self):
        """Get representation."""
        ret_str = '{'
        ret_str += ','.join([item.dumps() for item in self.items])
        ret_str += '}'

        return ret_str
