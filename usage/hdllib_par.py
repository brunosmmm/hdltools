"""Usage examples for parallel statements."""

from hdltools.abshdl.assign import HDLAssignment
from hdltools.hdllib.patterns import ParallelBlock, ClockedBlock
from hdltools.abshdl.signal import HDLSignal
from hdltools.abshdl.ifelse import HDLIfElse
from hdltools.abshdl.concat import HDLConcatenation
from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.vhdl.codegen import VHDLCodeGenerator
from hdltools.abshdl.highlvl import HDLBlock

if __name__ == "__main__":

    # create some signals
    clk = HDLSignal("reg", "clk")
    rst = HDLSignal("comb", "rst")
    en = HDLSignal("comb", "en")
    out = HDLSignal("reg", "out", size=8)
    feedback = HDLSignal("comb", "feedback")

    # parallel statements
    @ParallelBlock()
    def my_par(par, feedback, out, **kwargs):
        """Parallel statements."""
        # assign combinatorial signal
        par.add([feedback.assign((out[7] ^ out[3]).bool_neg())])

        @ClockedBlock(clk)
        def gen_lfsr(seq):
            concat = HDLConcatenation(
                out[6],
                out[5],
                out[4],
                out[3],
                out[2],
                out[1],
                out[0],
                feedback,
            )
            enif = HDLIfElse(en == 1, if_scope=out.assign(concat))
            rstif = HDLIfElse(
                rst == 1, if_scope=out.assign(0), else_scope=enif
            )

            seq.add(rstif)

        par.add([gen_lfsr()])

    print("*Parallel block*")
    print(my_par(feedback, out).dumps())

    print("*Verilog Output*")
    verilog_gen = VerilogCodeGenerator(indent=True)
    vhdl_gen = VHDLCodeGenerator()
    print(verilog_gen.dump_element(my_par(feedback, out)))
    print()
    print("*VHDL Output*")
    print(vhdl_gen.dump_element(my_par(feedback, out)))

    # try with python syntax
    @HDLBlock(**locals())
    @ParallelBlock()
    def my_par_highlvl():
        """High level mixed parallel and sequential block."""
        feedback = not (out[7] ^ out[3])

        @ClockedBlock(clk)
        def gen_lfsr():
            if rst == 1:
                out = 0
            else:
                if en == 1:
                    out = [out[0:6], feedback]

    print("*High level representation*")
    block, _, _ = my_par_highlvl()
    print(block.dumps())

    print("*Verilog Output*")
    print(verilog_gen.dump_element(block))
    print()
    print("*VHDL Output*")
    print(vhdl_gen.dump_element(block))
