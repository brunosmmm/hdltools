"""Usage of HDLModule as decorator."""

from hdltools.abshdl.module import HDLModule, input_port, output_port
from hdltools.hdllib.patterns import ParallelBlock, FSM
from hdltools.abshdl.signal import HDLSignal
from hdltools.abshdl.highlvl import HDLBlock
from hdltools.verilog.codegen import VerilogCodeGenerator


class TestFSM(FSM):
    """Test FSM."""

    def __state_zero(self, start):
        if start == 1:
            done_reg = 0
            state = 'one'

    def __state_one(self, counter):
        counter = counter + 1
        if counter == 4:
            state = 'two'

    def __state_two(self):
        done_reg = 1
        state = 'zero'


if __name__ == "__main__":

    HDLBlock.add_custom_block(TestFSM)

    @HDLModule('fsm', ports=[input_port('clk'),
                             input_port('rst'),
                             input_port('start'),
                             output_port('done')])
    def fsm_module(mod):
        """FSM Module."""
        # signals
        mod.add([
            HDLSignal('reg', 'state', size='defer'),
            HDLSignal('reg', 'done_reg'),
            HDLSignal('reg', 'counter', size=8)
        ])

        @HDLBlock(mod)
        @ParallelBlock()
        def fsm_body(clk, rst, done_reg, done, state):
            done = done_reg
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
