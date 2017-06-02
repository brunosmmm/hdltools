"""Test some more complex stimuli."""

from hdltools.sim import HDLSimulationObject
from hdltools.sim.simulation import HDLSimulation
from hdltools.vcd import VCDDump
from hdltools.vcd.generator import VCDGenerator
from collections import deque
import sys


class HDLSPIMaster(HDLSimulationObject):
    """SPI Master."""

    def __init__(self, identifier=None, clk_period=1,
                 tx_size=8, lsb_first=True):
        """Initialize."""
        super(HDLSPIMaster, self).__init__(identifier)
        # outputs
        self.ce = self.output('ce', initial=0)
        self.clk = self.output('clk', initial=0)
        self.do = self.output('do', initial=0)

        # data buffer
        self.queue = deque()

        # default logic behavior
        self.tx_size = tx_size
        self.clk_period = clk_period
        self.lsb_first = lsb_first

        # internal states
        self._state = 'idle'
        self._data = None
        self._size = None
        self._stop = False
        self._last_clk = 0

    def transmit(self, data, size=None, stop=True):
        """Transmit one block."""
        # put into queue for transmitting
        if size is None:
            size = self.tx_size
        sys.stderr.write('{} : stop = {}\n'.format(hex(data), stop))
        self.queue.appendleft([data, size, stop])

    def transmit_blocks(self, *data, block_size=None, stop=True):
        """Transmit a few blocks of same size."""
        if block_size is None:
            block_size = self.tx_size
        for index, block in enumerate(data):
            if stop is True:
                _stop = bool(index == len(data) - 1)
            else:
                _stop = False
            self.transmit(block, size=block_size, stop=_stop)

    def logic(self, input_states, **kwargs):
        """Perform internal logic."""
        if self._state == 'idle':
            if len(self.queue) > 0:
                self._state = 'transmit'
                # LSB first
                self._pos = 0
                self._data, self._size, stop = self.queue.pop()
                self.clk = False
                # check last block's stop
                if self._stop is True:
                    self.ce = False
                # store stop state for next block
                self._stop = stop
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
                    if self.lsb_first is True:
                        self.do = bool(self._data & (1 << self._pos))
                    else:
                        self.do = bool(self._data &
                                       (1 << (self._size - self._pos - 1)))

                    self._pos += 1
                    if self._pos > self._size - 1:
                        self._state = 'idle'
            else:
                # wait
                self._last_clk += 1


if __name__ == '__main__':

    sim = HDLSimulation()
    spi = HDLSPIMaster('spi')

    sim.add_stimulus(spi)

    spi.transmit_blocks(0x10, 0xAA)
    spi.transmit_blocks(0x80)
    dump = sim.simulate(100)

    vcd_dump = VCDDump('spi')
    vcd_dump.add_variables(**sim.report_signals())
    vcd_dump.load_dump(dump)
    vcd = VCDGenerator()

    print(vcd.dump_element(vcd_dump))
