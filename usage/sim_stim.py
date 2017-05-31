"""Test some more complex stimuli."""

from hdltools.sim import HDLSimulation, HDLSimulationObject, HDLSimulationLogic
from hdltools.vcd import VCDGenerator, VCDVariable
from collections import deque


class HDLSPIMaster(HDLSimulationObject):
    """SPI Master."""

    def __init__(self, identifier=None, clk_period=1, tx_size=8):
        """Initialize."""
        super(HDLSPIMaster, self).__init__(identifier)
        # outputs
        self.ce = self.output('ce')
        self.clk = self.output('clk')
        self.do = self.output('do')

        # data buffer
        self.queue = deque()

        # internal states
        self.tx_size = tx_size
        self.clk_period = clk_period
        self._state = 'idle'
        self._data = None
        self._last_clk = 0

    def transmit(self, *data):
        """Transmit some bytes."""
        # put into queue for transmitting
        self.queue.extendleft(data)

    def get_outputs(self, **kwargs):
        """Get output values."""
        return super(HDLSPIMaster, self).get_outputs(**kwargs)

    @HDLSimulationLogic(get_outputs)
    def next(self, **kwargs):
        """Perform internal logic."""
        if self._state == 'idle':
            if len(self.queue) > 0:
                self._state = 'transmit'
                # LSB first
                self._pos = 0
                self._data = self.queue.pop()
            else:
                self.ce = False
                self.do = False
                self.clk = False
                self._data = None
        elif self._state == 'transmit':
            # chip enable
            self.ce = True
            if self._last_clk >= self.clk_period - 1:
                # CPOL = 0
                self.clk = not self.clk
                self._last_clk = 0

                # data output
                if self.clk is True:
                    self.do = bool(self._data & (1 << self._pos))

                    self._pos += 1
                    if self._pos > self.tx_size:
                        self._state = 'idle'
            else:
                # wait
                self._last_clk += 1


if __name__ == '__main__':

    sim = HDLSimulation()
    spi = HDLSPIMaster('spi')

    sim.add_stimulus(spi)

    spi.transmit(0x10, 0xAA)
    print(sim.report_signals())
    dump = sim.simulate(100)
    print(dump)

    vcd = VCDGenerator()
