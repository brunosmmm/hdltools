"""Usage of HDLModule as decorator."""

from hdltools.abshdl.module import HDLModule, input_port, output_port
from hdltools.hdllib.patterns import ParallelBlock, ClockedBlock
from hdltools.abshdl.signal import HDLSignal
from hdltools.abshdl.highlvl import HDLBlock
from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.vhdl.codegen import VHDLCodeGenerator


if __name__ == "__main__":

    @HDLModule(
        "lfsr",
        ports=[
            input_port("clk"),
            input_port("rst"),
            input_port("en"),
            output_port("out", 8),
        ],
    )
    def lfsr_module(mod):
        """LFSR Module."""
        # signals
        mod.add(
            [
                HDLSignal("comb", "feedback"),
                HDLSignal("reg", "out_reg", size=8),
            ]
        )

        @HDLBlock(mod)
        @ParallelBlock()
        def lfsr_body():
            """Build module body."""
            # assign feedback signal
            feedback = not (out[7] ^ out[3])
            # assign output
            out = out_reg

            # sequential block generation
            @ClockedBlock(clk)
            def gen_lfsr():
                if rst == 1:
                    out_reg = 0
                else:
                    if en == 1:
                        out_reg = [
                            out[6],
                            out[5],
                            out[4],
                            out[3],
                            out[2],
                            out[1],
                            out[0],
                            feedback,
                        ]
                    else:
                        out_reg = out_reg

        # add generated body to module
        mod.extend(*lfsr_body())

    # generate module
    lfsr = lfsr_module()

    print(lfsr.dumps())

    # generate code
    verilog_gen = VerilogCodeGenerator(indent=True)
    vhdl_gen = VHDLCodeGenerator()
    
    print("=" * 60)
    print("*LFSR Verilog Code*")
    print("=" * 60)
    print(verilog_gen.dump_element(lfsr))
    print()
    print("=" * 60)
    print("*LFSR VHDL Code*")
    print("=" * 60)
    print(vhdl_gen.dump_element(lfsr))
