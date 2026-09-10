"""Expression / parametric dump extras (HDLTOOLS-0001 B3/B7)."""

import pytest

from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.port import HDLModulePort
from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.vhdl.codegen import VHDLCodeGenerator


def test_hdl_expression_evaluate_missing_symbol_raises():
    """B7: unbound identifiers raise KeyError."""
    expr = HDLExpression("C_S_AXI_ADDR_WIDTH")
    with pytest.raises(KeyError):
        expr.evaluate()


def test_hdl_expression_evaluate_with_scope():
    """B7: provided scope evaluates successfully."""
    expr = HDLExpression("C_S_AXI_ADDR_WIDTH")
    assert expr.evaluate(C_S_AXI_ADDR_WIDTH=16) == 16


def test_dump_port_data_width_div_eight_verilog():
    """B3: WSTRB-style DATA_WIDTH/8 dumps symbolically (Verilog)."""
    port = HDLModulePort(
        direction="in",
        name="S_AXI_WSTRB",
        size=HDLExpression("C_S_AXI_DATA_WIDTH/8"),
    )
    out = VerilogCodeGenerator().dump_element(port)
    assert "S_AXI_WSTRB" in out
    assert "C_S_AXI_DATA_WIDTH/8" in out.replace(" ", "")


def test_dump_port_data_width_div_eight_vhdl():
    """B3: WSTRB-style DATA_WIDTH/8 dumps symbolically (VHDL)."""
    port = HDLModulePort(
        direction="in",
        name="S_AXI_WSTRB",
        size=HDLExpression("C_S_AXI_DATA_WIDTH/8"),
    )
    out = VHDLCodeGenerator().dump_element(port)
    assert "S_AXI_WSTRB" in out
    assert "C_S_AXI_DATA_WIDTH/8" in out.replace(" ", "")
