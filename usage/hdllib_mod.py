"""Usage of HDLModule as decorator."""

from hdltools.abshdl.module import HDLModule, input_port, output_port
from hdltools.hdllib.patterns import ParallelBlock, ClockedBlock
from hdltools.abshdl.signal import HDLSignal
from hdltools.abshdl.highlvl import HDLBlock
from hdltools.verilog.codegen import VerilogCodeGenerator


if __name__ == "__main__":

    @HDLModule('lfsr', ports=[input_port('clk'),
                              input_port('rst'),
                              input_port('en'),
                              output_port('out', 8)])
    def lfsr_module(mod):
        """LFSR Module."""
        # signals
        mod.add([
            HDLSignal('comb', 'feedback'),
            HDLSignal('reg', 'out_reg', size=8)
        ])

        @HDLBlock(mod)
        @ParallelBlock()
        def lfsr_body(clk, rst, en, feedback, out_reg, out):
            """Build module body."""
            # assign feedback signal
            feedback = not (out[7] ^ out[3])
            # assign output
            out = out_reg

            # sequential block generation
            @ClockedBlock(clk)
            def gen_lfsr(rst, en, feedback, out_reg, out):
                if rst == 1:
                    out_reg = 0
                else:
                    if en == 1:
                        out_reg = [out[6], out[5], out[4], out[3],
                                   out[2], out[1], out[0], feedback]
                    else:
                        out_reg = out_reg

        # add generated body to module
        mod.extend(lfsr_body())

    # generate module
    lfsr = lfsr_module()

    print(lfsr.dumps())

    # generate verilog code
    gen = VerilogCodeGenerator(indent=True)
    print(gen.dump_element(lfsr))
