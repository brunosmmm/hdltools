"""VHDL parametric-width regressions (HDLTOOLS-0001 Wave B)."""

from hdltools.abshdl.assign import HDLAssignment
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.port import HDLModulePort
from hdltools.abshdl.signal import HDLSignal
from hdltools.vhdl.codegen import VHDLCodeGenerator


def test_vhdl_dump_port_with_parametric_width():
    """B1: AXI-style parametric ports dump as symbolic downto slices."""
    gen = VHDLCodeGenerator()
    port = HDLModulePort(
        direction="in",
        name="S_AXI_AWADDR",
        size=HDLExpression("C_S_AXI_ADDR_WIDTH"),
    )

    out = gen.dump_element(port)

    assert "S_AXI_AWADDR" in out
    assert "C_S_AXI_ADDR_WIDTH" in out


def test_vhdl_dump_signal_with_parametric_width():
    """B1: AXI-style parametric signals dump with symbolic bounds."""
    gen = VHDLCodeGenerator()
    sig = HDLSignal(
        sig_type="reg",
        sig_name="axi_awaddr",
        size=HDLExpression("C_S_AXI_ADDR_WIDTH"),
    )

    out = gen.dump_element(sig, declaration_only=True)

    assert "axi_awaddr" in out
    assert "C_S_AXI_ADDR_WIDTH" in out


def test_vhdl_assign_to_parametric_width_signal():
    """B2: assignment to parametric-width signal must not KeyError."""
    gen = VHDLCodeGenerator()
    sig = HDLSignal(
        sig_type="reg",
        sig_name="axi_awaddr",
        size=HDLExpression("C_S_AXI_ADDR_WIDTH"),
    )
    assign = HDLAssignment(sig, 0)

    out = gen.dump_element(assign)

    assert "axi_awaddr" in out
    assert "<=" in out


def test_vhdl_sensitivity_any_without_signal():
    """IDEA-465: always @(*) / sens_type any dumps as process (all)."""
    from hdltools.abshdl.sens import HDLSensitivityDescriptor, HDLSensitivityList
    from hdltools.abshdl.seq import HDLSequentialBlock
    from hdltools.abshdl.assign import HDLAssignment

    sens = HDLSensitivityList()
    sens.add(HDLSensitivityDescriptor("any"))
    seq = HDLSequentialBlock(sensitivity_list=sens)
    out_sig = HDLSignal("reg", "dout", size=1)
    seq.add(HDLAssignment(out_sig, 0))

    out = VHDLCodeGenerator().dump_element(seq)
    assert "process" in out
    assert "all" in out


def test_vhdl_get_axi_mm_slave_full_dump():
    """IDEA-465: full axi mm slave entity dump must not TypeError on sens."""
    from hdltools.hdllib.aximm import get_axi_mm_slave

    slave = get_axi_mm_slave("tb_slave", 32, 2)
    out = VHDLCodeGenerator().dump_element(slave)
    assert "tb_slave" in out
    assert "process" in out
