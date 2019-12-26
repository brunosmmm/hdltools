"""Test some more complex stimuli."""

from hdltools.sim import HDLSimulationObject
from hdltools.sim.simulation import HDLSimulation
from hdltools.vcd import VCDDump
from hdltools.vcd.generator import VCDGenerator
from collections import deque
import sys


class HDLSPIMaster(HDLSimulationObject):
    """SPI Master."""

    def __init__(
        self, identifier=None, clk_period=1, tx_size=8, lsb_first=True
    ):
        """Initialize."""
        super().__init__(identifier)
        # outputs
        self.ce = self.output("ce", initial=0)
        self.clk = self.output("clk", initial=0)
        self.do = self.output("do", initial=0)
        self.di = self.input("di")

        # data buffer
        self.tx_queue = deque()
        self.rx_queue = deque()

        # default logic behavior
        self.tx_size = tx_size
        self.clk_period = clk_period
        self.lsb_first = lsb_first

        # internal states
        self._state = "idle"
        self._txdata = None
        self._rxdata = None
        self._size = None
        self._stop = False
        self._last_clk = 0

    def get_received_count(self):
        """Get received count."""
        return len(self.rx_queue)

    def get_received(self):
        """Get received data."""
        return self.rx_queue.pop()

    def transmit(self, data, size=None, stop=True):
        """Transmit one block."""
        # put into queue for transmitting
        if size is None:
            size = self.tx_size
        sys.stderr.write("{} : stop = {}\n".format(hex(data), stop))
        self.tx_queue.appendleft([data, size, stop])

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

    def logic(self, **kwargs):
        """Perform internal logic."""
        if self._state == "idle":
            if len(self.tx_queue) > 0:
                self._state = "transmit"
                # LSB first
                self._pos = 0
                self._txdata, self._size, stop = self.tx_queue.pop()
                self._rxdata = 0
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
                self._txdata = None
        elif self._state == "transmit":
            # chip enable
            self.ce = True
            if self._last_clk >= self.clk_period - 1:
                # CPOL = 0
                self.clk = not self.clk
                self._last_clk = 0

                # data output & input
                if self.clk is True:
                    if self.lsb_first is True:
                        self.do = bool(self._txdata & (1 << self._pos))
                        self._rxdata |= int(self.di) << self._pos
                    else:
                        self.do = bool(
                            self._txdata & (1 << (self._size - self._pos - 1))
                        )
                        self._rxdata |= (
                            int(self.di) << self._size - self._pos - 1
                        )

                    self._pos += 1
                    if self._pos > self._size - 1:
                        self._state = "idle"
                        self.rx_queue.appendleft(self._rxdata)
            else:
                # wait
                self._last_clk += 1


class HDLSpiSlave(HDLSimulationObject):
    """SPI Slave."""

    def __init__(
        self, identifier=None, clk_period=1, tx_size=8, lsb_first=True
    ):
        """Initialize."""
        super().__init__(identifier)
        # ports
        self.di = self.input("di")
        self.clk = self.input("clk")
        self.ce = self.input("ce")
        self.do = self.output("do")

        # default logic behavior
        self.tx_size = tx_size
        self.clk_period = clk_period
        self.lsb_first = lsb_first

        # internal state
        self._state = "idle"
        self._txdata = None
        self._rxdata = None
        self._pos = 0
        self.rx_queue = deque()
        self.tx_queue = deque()

    def input_changed(self, which_input, value):
        """Input change callback."""
        # print('changed: {} -> {}'.format(which_input,
        #                                  value))
        pass

    def logic(self, **kwargs):
        """Do internal logic."""
        if self._state == "idle":
            if self.ce is True:
                self._state = "receive"

                # first bit might already be there
                if self.clk is True:
                    self._pos = 1
                    self._rxdata = int(self.di)
                else:
                    self._pos = 0
                    self._rxdata = 0
        elif self._state == "receive":
            if self.clk is True:
                self._rxdata |= int(self.di) << self._pos

                self._pos += 1
                if self._pos > self.tx_size - 1:
                    self._state = "idle"
                    self.rx_queue.appendleft(self._rxdata)


if __name__ == "__main__":

    sim = HDLSimulation()
    mspi = HDLSPIMaster("mspi")
    sspi = HDLSpiSlave("sspi")

    sim.add_stimulus(mspi, sspi)
    sim.connect("mspi.clk", "sspi.clk")
    sim.connect("mspi.do", "sspi.di")
    sim.connect("mspi.ce", "sspi.ce")
    sim.connect("sspi.do", "mspi.di")

    print("Will send 3 bytes")
    mspi.transmit_blocks(0x10, 0xAA)
    mspi.transmit_blocks(0x80)
    print("Simulating 100 steps")
    dump = sim.simulate(100)

    vcd_dump = VCDDump("spi")
    vcd_dump.add_variables(**sim.report_signals())
    vcd_dump.load_dump(dump)
    vcd = VCDGenerator()
    print(vcd.dump_element(vcd_dump))

    rx_bytes = []
    while len(sspi.rx_queue) > 0:
        rx_bytes.append(hex(sspi.rx_queue.pop()))
    print("Slave got {} bytes: {}".format(len(rx_bytes), rx_bytes))
