"""Test some more complex stimuli."""

from hdltools.sim import HDLSimulationObject
from hdltools.sim.simulation import HDLSimulation
from hdltools.vcd.dump import VCDDump
from hdltools.vcd.generator import VCDGenerator
from collections import deque
import sys


class HDLSPIMaster(HDLSimulationObject):
    """SPI Master."""

    def __init__(
        self, identifier=None, clk_period=1, tx_size=8, lsb_first=True
    ):
        """Initialize."""
        super().__init__(
            identifier,
            clk_period=clk_period,
            tx_size=tx_size,
            lsb_first=lsb_first,
        )

    def initialstate(self):
        """Initial state."""
        self._state = "idle"
        self._txdata = None
        self._rxdata = None
        self._size = None
        self._stop = False
        self._last_clk = 0

    def structure(self):
        """Hierarchical structure."""
        self.add_output("ce", initial=0)
        self.add_output("clk", initial=0)
        self.add_output("do", initial=0)
        self.add_input("di")

        # data buffer
        self.tx_queue = deque()
        self.rx_queue = deque()

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

    NOP = 0x80
    READ_COUNT = 0x01
    ERASE_COUNT = 0x02

    def __init__(
        self, identifier=None, clk_period=1, tx_size=8, lsb_first=True
    ):
        """Initialize."""
        super().__init__(
            identifier,
            clk_period=clk_period,
            tx_size=tx_size,
            lsb_first=lsb_first,
        )

    def initialstate(self):
        """Initial state."""
        self._rxstate = "idle"
        self._txstate = "idle"
        self._txdata = None
        self._rxdata = None
        self._pos = 0
        self._txpos = 0
        self._count = 0

    def structure(self):
        """Hierarchical structure."""
        # ports
        self.add_input("di")
        self.add_input("clk")
        self.add_input("ce")
        self.add_output("do")

        # other
        self.rx_queue = deque()
        self.tx_queue = deque()

    def input_changed(self, which_input, value):
        """Input change callback."""
        print("changed: {} -> {}".format(which_input, value))

    def _byte_received(self, byte):
        """Byte received."""
        self.rx_queue.appendleft(byte)
        self._count += 1
        if byte == self.NOP:
            return
        if byte == self.READ_COUNT:
            self._txstate = "transmit"
            self.tx_queue.appendleft(self._count)
            return
        if byte == self.ERASE_COUNT:
            self._count = 0

    def logic(self, **kwargs):
        """Do internal logic."""
        if self._rxstate == "idle":
            if self.ce is True:
                self._rxstate = "receive"

                # first bit might already be there
                if self.clk is True:
                    self._pos = 1
                    self._rxdata = int(self.di)
                else:
                    self._pos = 0
                    self._rxdata = 0
        elif self._rxstate == "receive":
            if self.clk is True:
                if self.ce is False:
                    # abort
                    self._rxstate = "idle"
                    self._pos = 0
                    self._rxdata = 0
                else:
                    self._rxdata |= int(self.di) << self._pos

                    self._pos += 1
                    if self._pos > self.tx_size - 1:
                        self._rxstate = "idle"
                        self._byte_received(self._rxdata)

        # tx state machine
        if self._txstate == "transmit":
            if self.ce is True and self.clk is True:
                # do cool stuff
                self._txdata = self.tx_queue.pop()
                self._txstate = "transmitting"
                self._txpos = 0
            else:
                self._txstate = "idle"
                self._txpos = 0
        elif self._txstate == "transmitting":
            if self.clk is True:
                self.do = bool(self._txdata & (1 << self._txpos))
                self._txpos += 1
                if self._txpos == 8:
                    self._txstate = "idle"


if __name__ == "__main__":

    sim = HDLSimulation()
    mspi = HDLSPIMaster("mspi")
    sspi = HDLSpiSlave("sspi")

    sim.add_stimulus(mspi, sspi)
    sim.connect("mspi.clk", "sspi.clk")
    sim.connect("mspi.do", "sspi.di")
    sim.connect("mspi.ce", "sspi.ce")
    sim.connect("sspi.do", "mspi.di")

    print("Will send 3 bytes (NOP)")
    mspi.transmit_blocks(0x80, 0x80, 0x80)
    # read count
    mspi.transmit_blocks(0x01, 0x80)
    # erase count
    mspi.transmit_blocks(0x02)
    print("Simulating 100 steps")
    dump = sim.simulate(100)

    vcd_dump = VCDDump("spi")
    vcd_dump.add_variables(**sim.signals)
    vcd_dump.load_dump(dump)
    vcd = VCDGenerator()
    with open("spi.vcd", "w") as dump:
        dump.write(vcd.dump_element(vcd_dump))

    rx_bytes = []
    while len(sspi.rx_queue) > 0:
        rx_bytes.append(hex(sspi.rx_queue.pop()))
    print("Slave got {} bytes: {}".format(len(rx_bytes), rx_bytes))
