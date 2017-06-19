"""Concatenation."""

from . import HDLObject
from .expr import HDLExpression
from .signal import HDLSignal, HDLSignalSlice
from .const import HDLIntegerConstant


class HDLConcatenation(HDLObject):
    """Concatenation of HDLObjects."""

    def __init__(self, *args, size=None, direction='rl'):
        """Initialize."""
        self.items = []
        self.size = size
        self.direction = direction

        if self.size is not None:
            # fill with zeros
            for i in range(size):
                self.append(HDLIntegerConstant(0, size=1,
                                               radix='b'))

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

    def _find_offset(self, offset):
        """Find actual offset in item list."""
        _offset = 0
        for index, item in enumerate(self.items):
            if _offset == offset:
                return index
            _offset += len(item)

    def insert(self, item, offset, size=None):
        """Add item with location offset."""
        _item = self._check_item(item)
        try:
            item_size = len(_item)
        except:
            item_size = None

        if item_size is None:
            if size is None:
                raise ValueError('could not determine item size '
                                 'and manual size not provided')
            else:
                item_size = size

        # remove placeholders
        actual_offset = self._find_offset(offset)
        if actual_offset is None:
            raise ValueError('could not determine insertion offset')
        del self.items[actual_offset:actual_offset+item_size-1]
        # insert item
        self.items[actual_offset] = _item

    def __len__(self):
        """Get length."""
        total_length = 0
        for item in self.items:
            total_length += len(item)

        return total_length

    def pack(self):
        """Pack constants together."""
        items = []
        last_item = None
        current_pos = 0
        for item in self.items:
            if item.from_type != 'const':
                if current_pos != 0:
                    items.append(HDLExpression(last_item,
                                               size=current_pos,
                                               radix='b'))
                current_pos = 0
                last_item = None
                # append item also
                items.append(item)
            else:
                if last_item is None:
                    last_item = item.evaluate()
                    current_pos = 1
                else:
                    last_item |= item.evaluate() << current_pos
                    current_pos += 1

        if current_pos != 0:
            items.append(HDLExpression(last_item,
                                       size=current_pos,
                                       radix='b'))

        return HDLConcatenation(*items)

    def dumps(self):
        """Get representation."""
        if self.direction == 'rl':
            items = self.items[::-1]
        elif self.direction == 'lr':
            items = self.items
        else:
            raise ValueError('undefined order')

        ret_str = '{'
        ret_str += ','.join([item.dumps() for item in items])
        ret_str += '}'

        return ret_str
