"""Usage examples for generating sequential blocks."""

from hdltools.hdllib.patterns import (ClockedBlock, SequentialBlock,
                                      ClockedRstBlock)
from hdltools.abshdl.assign import HDLAssignment
from hdltools.abshdl.signal import HDLSignal
from hdltools.abshdl.ifelse import HDLIfElse


if __name__ == "__main__":

    # declare some signals
    clk = HDLSignal('reg', 'clk')
    rst = HDLSignal('comb', 'rst')
    counter = HDLSignal('reg', 'counter')

    # manually created sequential block using clocked
    @SequentialBlock(['rise', clk])
    def my_counter_manual(seq, clk, rst, counter, **kwargs):
        """Test SequentialBlock."""
        ifelse = HDLIfElse(rst == 1,
                           if_scope=counter.assign(0),
                           else_scope=counter.assign(counter+1))
        seq.add(ifelse)

    print('*Using SequentialBlock*')
    print(my_counter_manual(clk, rst, counter).dumps())

    # a clocked block
    @ClockedBlock(clk)
    def my_counter_simple(seq, clk, rst, counter, **kwargs):
        """Test block, manually insert reset if-else."""
        ifelse = HDLIfElse(rst == 1,
                           if_scope=counter.assign(0),
                           else_scope=counter.assign(counter+1))
        seq.add(ifelse)

    print('*Using ClockedBlock*')
    print(my_counter_simple(clk, rst, counter).dumps())

    # a block with clock and reset
    @ClockedRstBlock(clk, rst)
    def my_counter(seq, counter, **kwargs):
        """Test block with clock and reset."""
        # get if-else statement
        _, (_, ifelse) = seq.find_by_tag('rst_if')
        # populate if-else statement
        ifelse.add_to_if_scope(counter.assign(0))
        ifelse.add_to_else_scope(counter.assign(counter+1))

    print('*Using CLockedRstBlock*')
    print(my_counter(counter).dumps())
