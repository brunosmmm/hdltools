"""Usage of HDLModule as decorator."""

from hdltools.abshdl.module import HDLModule, input_port, output_port
from hdltools.hdllib.patterns import ParallelBlock, FSM
from hdltools.abshdl.signal import HDLSignal
from hdltools.abshdl.highlvl import HDLBlock
from hdltools.verilog.codegen import VerilogCodeGenerator


class TestFSM(FSM):
    """Test FSM."""

    def __state_zero(self):
        pass

    def __state_one(self):
        pass

    def __state_two(self):
        pass


if __name__ == "__main__":

    HDLBlock.add_custom_block(TestFSM)

    @HDLModule('fsm', ports=[input_port('clk'),
                             input_port('rst'),
                             output_port('out', 2)])
    def fsm_module(mod):
        """FSM Module."""
        # signals
        mod.add([
            HDLSignal('reg', 'state', size='defer'),
            HDLSignal('reg', 'out_reg', size=8)
        ])

        @HDLBlock(mod)
        @ParallelBlock()
        def fsm_body(clk, rst, out_reg, out, state):
            out = out_reg
            # sequential block generation

            @TestFSM(clk, rst, state, initial='zero')
            def myfsm():
                pass

        # add generated body to module
        mod.extend(*fsm_body())

    # generate module
    fsm = fsm_module()

    print(fsm.dumps())

    # generate verilog code
    gen = VerilogCodeGenerator(indent=True)
    print(gen.dump_element(fsm))
