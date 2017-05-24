"""Constants."""

from . import HDLValue
import math


class HDLConstant(HDLValue):
    """Abstract class from which other constants inherit."""

    def __init__(self, **kwargs):
        """Initialize."""
        # save kwargs
        self.optional_args = kwargs


class HDLStringConstant(HDLConstant):
    """String constant value."""

    pass


class HDLIntegerConstant(HDLConstant):
    """A constant value."""

    def __init__(self, value, size=None, **kwargs):
        """Initialize.

        Args
        ----
        value: int
            A constant value
        """
        super(HDLIntegerConstant, self).__init__(**kwargs)

        # TODO: if size is not None, test legality, else
        # calculate minimum size and attribute it
        if size is not None:
            # check size
            if self.value_fits_width(size, value) is True:
                self.size = size
            else:
                raise ValueError('given value does not fit in given size')
        else:
            # attribute size
            self.size = self.minimum_value_size(value)

        self.value = value

    def evaluate(self, **kwargs):
        """Evaluate."""
        return self.value

    def __repr__(self):
        """Get representation."""
        return str(self.value)

    def dumps(self):
        """Alias for __repr__."""
        return self.__repr__()

    def __sub__(self, other):
        """Subtract two constants, return a new one.

        Args
        ----
        other: int or HDLIntegerConstant
           Other value
        """
        if isinstance(other, (int, HDLIntegerConstant)):
            return HDLIntegerConstant(self.value - int(other))
        else:
            raise TypeError('can only subtract int and '
                            'HDLIntegerConstant types')

    def __abs__(self):
        """Return absolute value."""
        if self.value < 0:
            return HDLIntegerConstant(-self.value)
        else:
            return HDLIntegerConstant(self.value)

    def __int__(self):
        """Convert to integer."""
        return self.value

    def __add__(self, other):
        """Add two constants, return a new one.

        Args
        ----
        other: int, HDLIntegerConstant
           Other value to add
        """
        if isinstance(other, (int, HDLIntegerConstant)):
            return HDLIntegerConstant(self.value + int(other))
        else:
            raise TypeError('can only add int and HDLIntegerConstant types')

    def __radd__(self, other):
        """Reverse add. Uses __add__."""
        return self.__add__(other)

    def __mul__(self, other):
        """Multiply two constants."""
        if isinstance(other, (int, HDLIntegerConstant)):
            return HDLIntegerConstant(self.value * int(other))
        else:
            raise TypeError('can only multiply int and'
                            ' HDLIntegerConstant types')

    def __eq__(self, other):
        """Equality test.

        Args
        ----
        other: int, HDLIntegerConstant
           Value to compare against
        """
        if isinstance(other, int):
            return bool(self.value == other)
        elif isinstance(other, HDLIntegerConstant):
            return bool(self.value == other.value)
        else:
            raise TypeError

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

    @staticmethod
    def minimum_value_size(value):
        """Get minimum number of bits needed to store value."""
        if value == 0:
            return 1
        else:
            return int(math.ceil(math.log2(float(value))))+1
