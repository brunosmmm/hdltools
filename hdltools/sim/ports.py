"""Simulation ports."""

from ..abshdl import HDLObject


class HDLSimulationPort(HDLObject):
    """Port representation."""

    def __init__(self, name, size=1, initial=0, change_cb=None):
        """Initialize."""
        self.name = name
        self.size = size
        self.initial = initial
        self._value = initial
        self._edge = None
        self._changed = False
        self._change_cb = change_cb

    def _value_change(self, value):
        """Record value change."""
        # for size of 1 bit only, detect edges
        if self.size == 1:
            if bool(self._value ^ value) is True:
                if bool(self._value) is True:
                    self._edge = "fall"
                else:
                    self._edge = "rise"
            else:
                self._edge = None
        else:
            self._changed = bool(self._value != value)

        if self._value != value:
            if self._change_cb is not None:
                self._change_cb(self.name, self._value)

        self._value = value

    def rising_edge(self):
        """Is rising edge."""
        if self.size != 1:
            raise IOError("only applicable to ports of size 1")
        return bool(self._edge == "rise")

    def falling_edge(self):
        """Is falling edge."""
        if self.size != 1:
            raise IOError("only applicable to ports of size 1")
        return bool(self._edge == "fall")

    def value_changed(self):
        """Get value changed or not."""
        return bool(self._edge is not None or self._changed is True)

    @property
    def value(self):
        """Get current value."""
        return self._value
