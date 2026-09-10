"""Switch / for / part_select codegen (HDLTOOLS-0001 B5/B6)."""

from hdltools.abshdl.assign import HDLAssignment
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.loop import HDLForLoop
from hdltools.abshdl.signal import HDLSignal
from hdltools.abshdl.switch import HDLCase, HDLSwitch
from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.vhdl.codegen import VHDLCodeGenerator


def test_switch_case_codegen_verilog_and_vhdl():
    """B5: switch/case dumps for both backends."""
    sel = HDLSignal("reg", "sel", size=2)
    out = HDLSignal("reg", "dout", size=1)
    switch = HDLSwitch(sel)
    switch.add_case(HDLCase(0, stmts=[HDLAssignment(out, 0)]))
    switch.add_case(HDLCase(1, stmts=[HDLAssignment(out, 1)]))

    vlog = VerilogCodeGenerator().dump_element(switch)
    assert "case" in vlog
    assert "endcase" in vlog
    assert "dout" in vlog

    vhdl = VHDLCodeGenerator().dump_element(switch)
    assert "case" in vhdl
    assert "when" in vhdl
    assert "dout" in vhdl


def test_for_loop_codegen_verilog():
    """B5: for-loop dumps for Verilog (aximm write-logic primitive)."""
    idx = HDLSignal("var", "byte_index", size=None, var_type="integer")
    init = HDLAssignment(idx, 0)
    stop = HDLExpression(idx) <= 3
    after = HDLAssignment(idx, HDLExpression(idx) + 1)
    loop = HDLForLoop(init, stop, after)
    body_sig = HDLSignal("reg", "scratch", size=8)
    loop.add_to_scope(HDLAssignment(body_sig, 0))

    vlog = VerilogCodeGenerator().dump_element(loop)
    assert "for" in vlog
    assert "byte_index" in vlog


def test_part_select_dump_verilog():
    """B6: part_select / signal slice dumps with bounds."""
    bus = HDLSignal("reg", "axi_awaddr", size=16)
    sliced = bus[7:0]
    vlog = VerilogCodeGenerator().dump_element(sliced)
    assert "axi_awaddr" in vlog
    assert "7" in vlog
    assert "0" in vlog


def test_symbolic_slice_dump_verilog():
    """B6: symbolic slice bounds dump without evaluating params."""
    bus = HDLSignal(
        "reg", "axi_awaddr", size=HDLExpression("C_S_AXI_ADDR_WIDTH")
    )
    # Use HDLSignalSlice via getitem with expression bounds if supported
    from hdltools.abshdl.signal import HDLSignalSlice
    from hdltools.abshdl.vector import HDLVectorDescriptor

    slic = HDLSignalSlice(
        bus, HDLVectorDescriptor(HDLExpression("ADDR_LSB+1"), HDLExpression("ADDR_LSB"))
    )
    vlog = VerilogCodeGenerator().dump_element(slic)
    assert "axi_awaddr" in vlog
    assert "ADDR_LSB" in vlog
