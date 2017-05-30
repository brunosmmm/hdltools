"""Usage examples for parallel statements."""

from hdltools.abshdl.assign import HDLAssignment
from hdltools.hdllib.patterns import ParallelBlock, ClockedBlock
from hdltools.abshdl.signal import HDLSignal, HDLSignalSlice
from hdltools.abshdl.ifelse import HDLIfElse
from hdltools.abshdl.concat import HDLConcatenation

if __name__ == "__main__":

    # create some signals
    clk = HDLSignal('reg', 'clk')
    rst = HDLSignal('comb', 'rst')
    en = HDLSignal('comb', 'en')
    out = HDLSignal('reg', 'out', size=8)
    feedback = HDLSignal('comb', 'feedback')

    # parallel statements
    @ParallelBlock()
    def my_par(par, feedback, out, **kwargs):
        """Parallel statements."""
        # assign combinatorial signal
        par.add([feedback.assign((out[7] ^ out[3]).bool_neg())])

        @ClockedBlock(clk)
        def gen_lfsr(seq, rst, en, feedback, out):
            concat = HDLConcatenation(out[6], out[5], out[4],
                                      out[3], out[2], out[1],
                                      out[0], feedback)
            enif = HDLIfElse(en == 1,
                             if_scope=out.assign(concat))
            rstif = HDLIfElse(rst == 1,
                              if_scope=out.assign(0),
                              else_scope=enif)

            seq.add(rstif)

        par.add([gen_lfsr(rst, en, feedback, out)])

    print('*Parallel block*')
    print(my_par(feedback, out).dumps())
