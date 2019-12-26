"""Stateful logic simulation elements."""

from ..abshdl import HDLObject


class HDLSimulationState(HDLObject):
    """Stateful logic element."""

    def __init__(self, name, size=1, initial=None):
        """Initialize."""
        self._name = name
        self._initial = initial
        self._size = size

    @property
    def name(self):
        """Get name."""
        return self._name

    @property
    def initial(self):
        """Get initial value."""
        return self._initial

    @property
    def size(self):
        """Get size."""
        return self._size
