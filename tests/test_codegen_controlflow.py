"""Switch / for / part_select codegen (HDLTOOLS-0001 B5/B6).

These assertions are intentional mutation checks: weak substring checks previously
accepted illegal Verilog (`for (byte_index <= 0; ...)`).
"""

from hdltools.abshdl.assign import HDLAssignment
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.loop import HDLForLoop
from hdltools.abshdl.signal import HDLSignal, HDLSignalSlice
from hdltools.abshdl.switch import HDLCase, HDLSwitch
from hdltools.abshdl.vector import HDLVectorDescriptor
from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.vhdl.codegen import VHDLCodeGenerator


def test_switch_case_codegen_verilog_and_vhdl():
    """B5: switch/case dumps concrete case arms for both backends."""
    sel = HDLSignal("reg", "sel", size=2)
    out = HDLSignal("reg", "dout", size=1)
    switch = HDLSwitch(sel)
    switch.add_case(HDLCase(0, stmts=[HDLAssignment(out, 0)]))
    switch.add_case(HDLCase(1, stmts=[HDLAssignment(out, 1)]))

    vlog = VerilogCodeGenerator().dump_element(switch)
    assert "case (sel)" in vlog or "case(sel)" in vlog.replace(" ", "")
    assert "endcase" in vlog
    assert "dout <=" in vlog

    vhdl = VHDLCodeGenerator().dump_element(switch)
    assert "case" in vhdl.lower()
    assert "when" in vhdl.lower()
    assert "dout" in vhdl


def test_for_loop_codegen_verilog_blocking_assign():
    """B5: for-loop indices must use blocking `=`, even via HDLAssignment default."""
    idx = HDLSignal("var", "byte_index", size=None, var_type="integer")
    # Deliberately use HDLAssignment(..., assign_type default "block") — the
    # production footgun. Codegen must still emit `=` for var targets.
    init = HDLAssignment(idx, 0)
    stop = HDLExpression(idx) <= 3
    after = HDLAssignment(idx, HDLExpression(idx) + 1)
    loop = HDLForLoop(init, stop, after)
    body_sig = HDLSignal("reg", "scratch", size=8)
    loop.add_to_scope(HDLAssignment(body_sig, 0))

    vlog = VerilogCodeGenerator().dump_element(loop)
    assert "for (" in vlog
    # Parse for (init; stop; step) — stop may contain `<=`; init/step must not.
    header = vlog[vlog.index("for (") + 5 : vlog.index(")")]
    init, stop, step = [p.strip() for p in header.split(";")]
    assert init.startswith("byte_index =") or init.startswith("byte_index=")
    assert "<=" not in init
    assert "byte_index" in stop  # comparison OK with <=
    assert step.startswith("byte_index =") or "byte_index =" in step
    assert "byte_index <=" not in step


def test_for_loop_codegen_via_signal_assign_api():
    """B5: signal.assign() path (production AXI style) also dumps blocking `=`."""
    idx = HDLSignal("var", "byte_index", size=None, var_type="integer")
    loop = HDLForLoop(
        idx.assign(0),
        HDLExpression(idx) <= 3,
        idx.assign(HDLExpression(idx) + 1),
    )
    loop.add_to_scope(HDLAssignment(HDLSignal("reg", "scratch", size=8), 0))
    vlog = VerilogCodeGenerator().dump_element(loop)
    header = vlog[vlog.index("for (") + 5 : vlog.index(")")]
    init, stop, step = [p.strip() for p in header.split(";")]
    assert "<=" not in init
    assert "byte_index <=" not in step
    assert "byte_index =" in init
    assert "byte_index =" in step


def test_part_select_dump_verilog():
    """B6: part_select / signal slice dumps with bounds."""
    bus = HDLSignal("reg", "axi_awaddr", size=16)
    sliced = bus[7:0]
    vlog = VerilogCodeGenerator().dump_element(sliced)
    assert "axi_awaddr[7:0]" in vlog.replace(" ", "")


def test_symbolic_slice_dump_verilog():
    """B6: symbolic slice bounds dump without evaluating params."""
    bus = HDLSignal(
        "reg", "axi_awaddr", size=HDLExpression("C_S_AXI_ADDR_WIDTH")
    )
    slic = HDLSignalSlice(
        bus,
        HDLVectorDescriptor(
            HDLExpression("ADDR_LSB+1"), HDLExpression("ADDR_LSB")
        ),
    )
    vlog = VerilogCodeGenerator().dump_element(slic)
    assert "axi_awaddr" in vlog
    assert "ADDR_LSB" in vlog
