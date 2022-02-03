"""Generate HDL model from simulation model."""

from hdltools.sim.hdl import HDLSimulationObjectScheduler
from hdltools.sim import HDLSimulationObject
from hdltools.sim.simulation import HDLSimulation
from hdltools.sim.primitives import ClockGenerator, OneshotSignal
from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.vcd.dump import VCDDump
from hdltools.vcd.generator import VCDGenerator


class Multiplexer(HDLSimulationObject):
    """A simple, combinatorial logic only object."""

    def structure(self):
        """Structural hierarchy."""
        self.add_input("a")
        self.add_input("b")
        self.add_output("y")
        self.add_input("sel")

    def logic(self, **kwargs):
        """Do logic."""
        # use one-line if statement
        # or sequential logic will be inferred
        self.y = self.b if self.sel is True else self.a


class LFSR(HDLSimulationObject):
    """Linear feedback shift register."""

    def structure(self):
        """Structural Hierarchy."""
        self.add_input("clk")
        self.add_input("rst")
        self.add_input("en")
        self.add_output("out", size=8)

    def logic(self, **kwargs):
        """Do internal logic."""
        feedback = not (self.out[7] ^ self.out[3])

        if self.rising_edge("clk"):
            if self.rst is True:
                self.out = 0b11001101
            else:
                if self.en is True:
                    self.out = [self.out[6:0], feedback]
                else:
                    self.out = self.out


if __name__ == "__main__":

    logic = Multiplexer("mux")
    sched = HDLSimulationObjectScheduler(logic)
    gen = VerilogCodeGenerator(indent=True)

    # verilog code
    print("*Multiplexer Verilog Code*")
    print(gen.dump_element(sched.schedule()[0]))

    lfsr = LFSR("lfsr")
    sched = HDLSimulationObjectScheduler(lfsr)
    print("*LFSR Verilog Code*")
    print(gen.dump_element(sched.schedule()[0]))

    ckgen = ClockGenerator("clk")
    reset = OneshotSignal("rst", 10, initial_value=True)
    enable = OneshotSignal("en", 20)
    sim = HDLSimulation()
    sim.add_stimulus(lfsr, reset, ckgen, enable)
    sim.connect("rst.sig", "lfsr.rst")
    sim.connect("clk.clk", "lfsr.clk")
    sim.connect("en.sig", "lfsr.en")
    dump = sim.simulate(100)

    vcd_dump = VCDDump("spi")
    vcd_dump.add_variables(**sim.signals)
    vcd_dump.load_dump(dump)
    vcd = VCDGenerator()

    with open("test.vcd", "w") as dump:
        dump.write(vcd.dump_element(vcd_dump))
