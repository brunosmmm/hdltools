"""Constants."""

from . import HDLValue


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

    def __init__(self, value, **kwargs):
        """Initialize.

        Args
        ----
        value: int
            A constant value
        """
        super(HDLIntegerConstant, self).__init__(**kwargs)
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
