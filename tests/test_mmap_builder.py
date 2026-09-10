"""MMBuilder / mmap tool regressions (HDLTOOLS-0001 Wave A)."""

from argparse import Namespace
from pathlib import Path

import pytest

from hdltools.hdllib.aximm import get_axi_mm_slave
from hdltools.mmap import parse_mmap_file
from hdltools.mmap.builder import MMBuilder
from hdltools.tools.common.mmap import MmapError, parse_param_replace_args
from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.vhdl.codegen import VHDLCodeGenerator

REPO_ROOT = Path(__file__).resolve().parents[1]
VIDEOCHK = REPO_ROOT / "assets" / "tests" / "videochk.mmap"


@pytest.fixture
def videochk_mmap():
    text, model = parse_mmap_file(str(VIDEOCHK))
    return MMBuilder(text).visit(model)


@pytest.mark.skipif(not VIDEOCHK.is_file(), reason="assets/tests/videochk.mmap missing")
def test_mmbuilder_videochk_semantics(videochk_mmap):
    """A3: visit() must expose registers, ports, and parameters."""
    mmap = videochk_mmap

    assert set(mmap.registers) == {"CONTROL", "FSIZE"}
    assert mmap.reg_size == 32

    assert mmap.ports["IRQ_EN"].direction == "out"
    assert mmap.ports["FREE_RUN"].direction == "out"
    assert mmap.ports["H_SIZE"].direction == "out"
    assert mmap.ports["V_SIZE"].direction == "out"
    assert mmap.ports["IRQ_ACK"].direction == "out"
    assert mmap.ports["IRQ_FLAG"].direction == "in"

    assert "MAX_HSIZE" in mmap.parameters
    assert "MAX_VSIZE" in mmap.parameters


@pytest.mark.skipif(not VIDEOCHK.is_file(), reason="assets/tests/videochk.mmap missing")
def test_get_axi_mm_slave_dump_smoke(videochk_mmap):
    """A4: axi slave construction dumps Verilog without KeyError; symbolic widths present."""
    slave = get_axi_mm_slave(
        "tb_slave", videochk_mmap.reg_size, len(videochk_mmap.registers)
    )
    port_names = {p.name for p in slave.ports}
    assert "S_AXI_ACLK" in port_names
    assert "S_AXI_AWADDR" in port_names

    vlog = VerilogCodeGenerator().dump_element(slave)
    assert "module tb_slave" in vlog
    assert "C_S_AXI_ADDR_WIDTH" in vlog
    assert "[(C_S_AXI_ADDR_WIDTH-1):0]" in vlog

    # Full VHDL entity dump of aximm still hits unrelated sens-list gaps;
    # parametric port dump is covered by test_vhdl_parametric.
    port = next(p for p in slave.ports if p.name == "S_AXI_AWADDR")
    vhdl_port = VHDLCodeGenerator().dump_element(port)
    assert "S_AXI_AWADDR" in vhdl_port
    assert "C_S_AXI_ADDR_WIDTH" in vhdl_port


def test_parse_param_replace_args_valid():
    """A5: key=value ints parse into a replacement map."""
    args = Namespace(param_replace=["MAX_HSIZE=4096", "MAX_VSIZE=2048"])
    assert parse_param_replace_args(args) == {
        "MAX_HSIZE": 4096,
        "MAX_VSIZE": 2048,
    }


def test_parse_param_replace_args_invalid():
    """A5: malformed replacements raise MmapError."""
    args = Namespace(param_replace=["MAX_HSIZE"])
    with pytest.raises(MmapError):
        parse_param_replace_args(args)


@pytest.mark.skipif(not VIDEOCHK.is_file(), reason="assets/tests/videochk.mmap missing")
def test_mmbuilder_param_replace_applied():
    """A5: visit(param_replace=...) overrides model parameters."""
    text, model = parse_mmap_file(str(VIDEOCHK))
    mmap = MMBuilder(text).visit(model, param_replace={"MAX_HSIZE": 1234})
    assert int(mmap.parameters["MAX_HSIZE"].value) == 1234
