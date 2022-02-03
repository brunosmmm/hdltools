"""Simulation primitives."""

from hdltools.sim import HDLSimulationObject


class ClockGenerator(HDLSimulationObject):
    """Simple clock generator."""

    def __init__(self, identifier, clk_period=1, clk_pol=False):
        """Initialize."""
        super().__init__(identifier, clk_period=clk_period, clk_pol=clk_pol)

    def initialstate(self):
        """Set initial state."""
        if self.clk_pol:
            self._state = "high"
        else:
            self._state = "low"

    def structure(self):
        """Set up structure."""
        self.add_output("clk", initial=1 if self.clk_pol else 0)

    def logic(self, **kwargs):
        """Describe simulation logic."""
        if self._state == "low":
            self._state = "high"
            self.clk = True
        else:
            self._state = "low"
            self.clk = False


class OneshotSignal(HDLSimulationObject):
    """Oneshot signal generator."""

    def __init__(self, identifier, wait_for, initial_value=False):
        """Initialize."""
        super().__init__(
            identifier, wait_for=wait_for, initial_value=initial_value
        )

    def initialstate(self):
        """Set initial state."""
        self._count = 0

    def structure(self):
        """Set up structure."""
        self.add_output("sig", initial=True if self.initial_value else False)

    def logic(self, **kwargs):
        """Describe simulation logic."""
        if self._count < self.wait_for:
            self._count += 1
        else:
            if self.initial_value:
                self.sig = False
            else:
                self.sig = True
