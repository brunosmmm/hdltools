"""E2E regression for axi_slave_builder (HDLTOOLS-0001 / A1)."""

import sys
from pathlib import Path

import pytest

from hdltools.tools.axi_slave_builder import main

REPO_ROOT = Path(__file__).resolve().parents[1]
VIDEOCHK = REPO_ROOT / "assets" / "tests" / "videochk.mmap"


@pytest.mark.skipif(not VIDEOCHK.is_file(), reason="assets/tests/videochk.mmap missing")
def test_axi_slave_builder_videochk_mmap(tmp_path, monkeypatch, capsys):
    """Full mmap→Verilog dump must succeed with AXI parametric widths intact."""
    out = tmp_path / "aximm_slave.v"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "axi_slave_builder",
            str(VIDEOCHK),
            "-o",
            str(out),
            "--modname",
            "aximm_slave",
        ],
    )

    main()

    text = out.read_text()
    assert "module aximm_slave" in text
    assert "C_S_AXI_ADDR_WIDTH" in text
    assert "S_AXI_AWADDR" in text
    assert "[(C_S_AXI_ADDR_WIDTH-1):0]" in text
    assert "REG_CONTROL" in text
    assert "REG_FSIZE" in text
