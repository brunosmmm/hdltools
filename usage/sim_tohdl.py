"""Generate HDL model from simulation model."""

from hdltools.sim.hdl import HDLSimulationObjectScheduler
from hdltools.sim import HDLSimulationObject
from hdltools.verilog.codegen import VerilogCodeGenerator


class Multiplexer(HDLSimulationObject):
    """A simple, combinatorial logic only object."""

    def __init__(self, identifier):
        """Initialize."""
        super().__init__(identifier)
        self.a = self.input('a')
        self.b = self.input('b')
        self.y = self.output('y')
        self.sel = self.input('sel')

    def logic(self, **kwargs):
        """Do logic."""
        # use one-line if statement
        # or sequential logic will be inferred
        self.y = self.b if self.sel is True else self.a


if __name__ == "__main__":

    logic = Multiplexer('mux')
    sched = HDLSimulationObjectScheduler(logic)
    gen = VerilogCodeGenerator()

    # verilog code
    print('*Multiplexer Verilog Code*')
    print(gen.dump_element(sched.schedule()))
