"""Vector descriptor."""

from . import HDLObject
from .expr import HDLExpression
from .const import HDLIntegerConstant
import math


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
        if not isinstance(left_size, (int, HDLExpression)):
            raise TypeError('only int or HDLExpression allowed as size')

        if not isinstance(right_size, (int, HDLExpression)):
            if right_size is None:
                # take this as zero
                right_size = 0
            else:
                raise TypeError('only int or HDLExpression allowed as size')

        if not isinstance(stored_value, (int, (type(None)))):
            raise TypeError('stored_value can only be int or None')

        # if integer, check bounds
        self._check_value(right_size)
        self._check_value(left_size)

        if isinstance(left_size, int):
            self.left_size = HDLIntegerConstant(left_size)
        else:
            self.left_size = left_size
        if isinstance(right_size, int):
            self.right_size = HDLIntegerConstant(right_size)
        else:
            self.right_size = right_size

        # check for value legality
        if stored_value is not None:
            if self.value_fits_width(len(self), stored_value) is True:
                self.stored_value = stored_value
            else:
                raise ValueError('vector cannot hold passed stored_value')

    def _check_value(self, value):
        if isinstance(value, int):
            if value < 0:
                raise ValueError('only positive values allowed for sizes')

    def evaluate_right(self, eval_scope={}):
        """Evaluate right side size."""
        return self.right_size.evaluate(**eval_scope)

    def evaluate_left(self, eval_scope={}):
        """Evaluate left side size."""
        return self.left_size.evaluate(**eval_scope)

    def evaluate(self, eval_scope={}):
        """Evaluate both sides."""
        return (self.evaluate_left(eval_scope),
                self.evaluate_right(eval_scope))

    def __len__(self):
        """Get vector length."""
        return abs(int(self.left_size) - int(self.right_size)) + 1

    def __repr__(self, eval_scope=None):
        """Represent."""
        if eval_scope is not None:
            left_size = self.evaluate_left(eval_scope)
            right_size = self.evaluate_right(eval_scope)
        else:
            left_size = self.left_size
            right_size = self.right_size
        return '[{}:{}]'.format(left_size, right_size)

    def dumps(self, eval_scope=None):
        """Dump description to string."""
        return self.__repr__(eval_scope)

    @staticmethod
    def value_fits_width(width, value):
        """Check if a value fits in a vector.

        Args
        ----
        width: int
           Bit Vector width
        value: int
           The value
        """
        return bool(value <= (int(math.pow(2, width)) - 1))
