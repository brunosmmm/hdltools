"""Usage of HDLModule as decorator."""

from hdltools.abshdl.module import HDLModule, input_port, output_port
from hdltools.hdllib.patterns import ParallelBlock
from hdltools.hdllib.fsm import FSM
from hdltools.abshdl.signal import HDLSignal
from hdltools.abshdl.highlvl import HDLBlock
from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.vhdl.codegen import VHDLCodeGenerator


class TestFSM(FSM):
    """Test FSM."""

    def __state_zero(self, start):
        if start == 1:
            done_reg = 0
            self.state = "one"

    def __state_one(self, counter):
        counter = counter + 1
        if counter == 4:
            self.state = "two"

    def __state_two(self):
        done_reg = 1
        self.state = "zero"


if __name__ == "__main__":

    HDLBlock.add_custom_block(TestFSM)

    @HDLModule(
        "fsm",
        ports=[
            input_port("clk"),
            input_port("rst"),
            input_port("start"),
            output_port("done"),
        ],
    )
    def fsm_module(mod, counter_size=8):
        """FSM Module."""
        # signals
        mod.add(
            [
                HDLSignal("reg", "state", size="defer"),
                HDLSignal("reg", "state2", size="defer"),
                HDLSignal("reg", "done_reg"),
                HDLSignal("reg", "counter", size=counter_size),
            ]
        )

        @HDLBlock(mod)
        @ParallelBlock()
        def fsm_body():
            done = done_reg
            # sequential block generation

            @TestFSM(clk, rst, state, initial="zero")
            def myfsm():
                pass

            # TODO: state variable cannot be the same, detect and prevent
            # in generation code
            @TestFSM(clk, rst, state2, initial="zero")
            def mysecondfsm():
                pass

        # add generated body to module
        mod.extend(*fsm_body())

    print("* Module *")
    # generate module
    # FIXME: doesnt work with keyword arguments
    fsm = fsm_module(16)

    print(fsm.dumps())

    # generate code
    verilog_gen = VerilogCodeGenerator(indent=True)
    vhdl_gen = VHDLCodeGenerator()
    
    print("=" * 60)
    print("*FSM Verilog Code*")
    print("=" * 60)
    print(verilog_gen.dump_element(fsm))
    print()
    print("=" * 60)
    print("*FSM VHDL Code*")
    print("=" * 60)
    print(vhdl_gen.dump_element(fsm))
