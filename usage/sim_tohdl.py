"""Generate HDL model from simulation model."""

from hdltools.sim.hdl import HDLSimulationObjectScheduler
from hdltools.sim import HDLSimulationObject
from hdltools.verilog.codegen import VerilogCodeGenerator


class Multiplexer(HDLSimulationObject):
    """A simple, combinatorial logic only object."""

    def __init__(self, identifier):
        """Initialize."""
        super().__init__(identifier)
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

    def __init__(self, identifier):
        """Initialize."""
        super().__init__(identifier)
        self.add_input("clk")
        self.add_input("rst")
        self.add_input("en")
        self.add_output("out", size=8)

    def logic(self, **kwargs):
        """Do internal logic."""
        feedback = not (self.out[7] ^ self.out[3])

        if self.rising_edge("clk"):
            if self.rst is True:
                self.out = 0
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
