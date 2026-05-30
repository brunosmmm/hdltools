"""Vector descriptor."""

from hdltools.abshdl import HDLObject
import hdltools.abshdl.expr as expr
from hdltools.abshdl.const import HDLIntegerConstant
import hdltools.abshdl.signal as signal


class HDLVectorDescriptor(HDLObject):
    """Describe a vector signal."""

    def __init__(self, left_size, right_size=None, stored_value=None):
        """Initialize.

        Args
        ----
        left_size: int
           Size on the left of vector declaration
        right_size: int, NoneType
           Size on the right of vector declaration
        stored_value: int, NoneType
           A stored value
        """
        if not isinstance(
            left_size,
            (
                int,
                HDLIntegerConstant,
                expr.HDLExpression,
                signal.HDLSignal,
                signal.HDLSignalPartSelect,
            ),
        ):
            raise TypeError(
                "only int or HDLExpression allowed as size,"
                " got: {}".format(left_size.__class__.__name__)
            )

        if not isinstance(
            right_size,
            (int, HDLIntegerConstant, expr.HDLExpression, signal.HDLSignal),
        ):
            if right_size is None:
                # take this as zero
                right_size = 0
            else:
                raise TypeError("only int or HDLExpression allowed as size")

        if isinstance(left_size, signal.HDLSignal):
            if left_size.sig_type not in ("const", "var"):
                raise ValueError(
                    "slices can only contain compile-time "
                    "determinable values"
                )
        if isinstance(right_size, signal.HDLSignal):
            if right_size.sig_type not in ("const", "var"):
                raise ValueError(
                    "slices can only contain compile-time "
                    "determinable values"
                )

        if not isinstance(stored_value, (int, (type(None)))):
            raise TypeError("stored_value can only be int or None")

        # if integer, check bounds
        self._check_value(right_size)
        self._check_value(left_size)

        self.part_select = False
        if isinstance(left_size, (int, HDLIntegerConstant, signal.HDLSignal)):
            self.left_size = expr.HDLExpression(left_size)
        elif isinstance(left_size, signal.HDLSignalPartSelect):
            self.left_size = expr.HDLExpression(left_size.offset)
            self.part_select_length = left_size.length
            self.part_select = True
        else:
            self.left_size = left_size
        if isinstance(right_size, (int, HDLIntegerConstant, signal.HDLSignal)):
            self.right_size = expr.HDLExpression(right_size)
        else:
            self.right_size = right_size

        # check for value legality
        if stored_value is not None:
            if (
                HDLIntegerConstant.value_fits_width(len(self), stored_value)
                is True
            ):
                self.stored_value = stored_value
            else:
                raise ValueError("vector cannot hold passed stored_value")

    def _check_value(self, value):
        if isinstance(value, int):
            if value < 0:
                raise ValueError("only positive values allowed for sizes")

    def evaluate_right(self, **eval_scope):
        """Evaluate right side size."""
        return self.right_size.evaluate(**eval_scope)

    def evaluate_left(self, **eval_scope):
        """Evaluate left side size."""
        return self.left_size.evaluate(**eval_scope)

    def evaluate(self, **eval_scope):
        """Evaluate both sides."""
        return (
            self.evaluate_left(**eval_scope),
            self.evaluate_right(**eval_scope),
        )

    def get_bounds(self):
        """Get bounds."""
        return (self.left_size, self.right_size)

    def __len__(self):
        """Get vector length."""
        return abs(int(self.left_size) - int(self.right_size)) + 1

    def __repr__(self, eval_scope=None):
        """Represent."""
        if eval_scope is not None:
            left_size = self.evaluate_left(**eval_scope)
            right_size = self.evaluate_right(**eval_scope)
        else:
            left_size = self.left_size
            right_size = self.right_size
        if self.part_select is False:
            return f"[{left_size}:{right_size}]"
        return "[{}:{:+}]".format(left_size, self.part_select_length)

    def dumps(self, eval_scope=None):
        """Dump description to string."""
        return self.__repr__(eval_scope)
