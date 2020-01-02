"""Concatenation."""

from . import HDLObject
from .const import HDLIntegerConstant
import hdltools.abshdl.expr
import hdltools.abshdl.signal


class HDLConcatenation(HDLObject):
    """Concatenation of HDLObjects."""

    def __init__(self, value, *args, size=None, direction="rl"):
        """Initialize."""
        self.items = []
        self.size = size

        if direction not in ("lr", "rl"):
            raise ValueError("direction must be either lr or rl")

        self._direction = direction

        if not args:
            # nothing to concatenate
            raise ValueError("concatenation takes at least 2 elements")

        if self.size is not None:
            # fill with zeros
            for i in range(size-len(args)-1):
                self.append(HDLIntegerConstant(0, size=1, radix="b"))

        # HDLExpression is unconstrained!
        self.append(value)
        for arg in args:
            self.append(arg)

    @property
    def direction(self):
        """Get direction."""
        return self._direction

    def _check_item(self, item):
        if isinstance(item, hdltools.abshdl.expr.HDLExpression):
            arg_expr = item
        elif isinstance(
            item,
            (
                hdltools.abshdl.signal.HDLSignal,
                hdltools.abshdl.signal.HDLSignalSlice,
                HDLIntegerConstant,
                int,
            ),
        ):
            arg_expr = hdltools.abshdl.expr.HDLExpression(item)
        else:
            raise TypeError(
                "Only types convertible to HDLExpression"
                " allowed, "
                'not "{}"'.format(item.__class__.__name__)
            )

        return arg_expr

    def append(self, item):
        """Add item."""
        if self.direction == "lr":
            self.appendright(item)
        else:
            self.appendleft(item)

    def appendright(self, item):
        """Append right."""
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
        if self.size is None:
            raise ValueError(
                "cannot insert into offset without "
                "predetermined concatenation size"
            )

        _item = self._check_item(item)
        try:
            item_size = len(_item)
        except:
            item_size = None

        if item_size is None:
            if size is None:
                raise ValueError(
                    "could not determine item size "
                    "and manual size not provided"
                )
            else:
                item_size = size

        # remove placeholders
        actual_offset = self._find_offset(offset)
        if actual_offset is None:
            raise ValueError("could not determine insertion offset")
        del self.items[actual_offset : actual_offset + item_size - 1]
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
            if item.from_type != "const":
                if current_pos != 0:
                    items.append(
                        hdltools.abshdl.expr.HDLExpression(
                            last_item, size=current_pos, radix="b"
                        )
                    )
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
            items.append(
                hdltools.abshdl.expr.HDLExpression(
                    last_item, size=current_pos, radix="b"
                )
            )

        return HDLConcatenation(*items)

    def dumps(self):
        """Get representation."""
        ret_str = "{"
        ret_str += ",".join([item.dumps() for item in self.items])
        ret_str += "}"

        return ret_str
