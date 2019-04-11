"""Simulation Library."""

from ..sim import HDLSimulationObject
from ..abshdl.expr import HDLExpression


class HDLSimulationConstant(HDLSimulationObject):
    """Constant value."""

    def __init__(self, value, size=None):
        """Initialize."""
        self.value = self._get_constant(value, size)

    def next(self):
        """Return the same value always."""
        for x in iter(int, 1):
            yield self.value


class HDLSimulationReset(HDLSimulationObject):
    """Reset generator."""

    def __init__(self, rst_delay, rst_lvl=1):
        """Initialize."""
        super().__init__()
        self.delay = self._get_constant(rst_delay)
        self.lvl = HDLExpression(rst_lvl)

    def next(self):
        """Generate value."""
        # assert reset
        for i in range(self.delay.value):
            yield bool(self.lvl)
        # deassert forever
        for x in iter(int, 1):
            yield bool(not self.lvl)


class HDLSimulationClock(HDLSimulationObject):
    """Clock generator."""

    def __init__(self, period, start_pol=1):
        """Initialize."""
        super().__init__()
        self.start_pol = self._get_constant(start_pol)
        self.period = self._get_constant(period)
        self._level = bool(self.start_pol)
        self._last_edge = 0

    def next(self):
        """Generate values."""
        for x in iter(int, 1):
            if self._last_edge > self.period - 1:
                self._level = not self._level
                self._last_edge = 1
            else:
                self._last_edge += 1
            yield self._level
