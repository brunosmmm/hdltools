"""Test command-line tools basic functionality."""

import json
import sys
import tempfile
from pathlib import Path

import pytest

from hdltools.tools.fnboundary import main as fnboundary_main
from hdltools.tools.inputgen import main as inputgen_main
from hdltools.tools.vcdcmp import main as vcdcmp_main
from hdltools.tools.vcdhier import main as vcdhier_main
from hdltools.tools.vgc import main as vgc_main

REPO = Path(__file__).resolve().parents[1]
INPUT1_VG = REPO / "assets" / "tests" / "input1.vg"
USAGE_VCD = REPO / "usage" / "test.vcd"


class TestCliTools:
    """Test basic CLI tool functionality via module main()."""

    def test_vgc_help(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["vgc", "--help"])
        with pytest.raises(SystemExit) as exc:
            vgc_main()
        assert exc.value.code == 0
        assert "usage" in capsys.readouterr().out.lower()

    def test_vcdcmp_help(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["vcdcmp", "--help"])
        with pytest.raises(SystemExit) as exc:
            vcdcmp_main()
        assert exc.value.code == 0
        out = capsys.readouterr().out.lower()
        assert "usage" in out or "vcd" in out

    def test_vgc_with_assets_input1(self, tmp_path, monkeypatch):
        """Valid .vg must exit successfully and write JSON."""
        if not INPUT1_VG.is_file():
            pytest.skip("assets/tests/input1.vg missing")
        out = tmp_path / "out.json"
        monkeypatch.setattr(
            sys, "argv", ["vgc", str(INPUT1_VG), "--output", str(out)]
        )
        vgc_main()
        assert out.is_file()
        json.loads(out.read_text())

    def test_vcdhier_with_sample_vcd(self, monkeypatch, capsys):
        """vcdhier dumphier on usage/test.vcd must succeed."""
        if not USAGE_VCD.is_file():
            pytest.skip("usage/test.vcd missing")
        monkeypatch.setattr(
            sys, "argv", ["vcdhier", str(USAGE_VCD), "dumphier"]
        )
        vcdhier_main()
        assert capsys.readouterr().out.strip()

    def test_fnboundary_with_valid_objdump(self, tmp_path, monkeypatch, capsys):
        """Valid objdump fixture must list functions with exit success."""
        asm = tmp_path / "sample.asm"
        asm.write_text(
            "objdump: file format elf32-littlearm\n"
            "Disassembly of section .text:\n"
            "00001000 <_start>:\n"
            "1000: e3a00000 mov r0, #0\n"
            "00001008 <main>:\n"
            "1008: e92d4000 push {lr}\n"
        )
        monkeypatch.setattr(sys, "argv", ["fnboundary", "--list-fns", str(asm)])
        fnboundary_main()
        out = capsys.readouterr().out
        assert "_start" in out
        assert "main" in out

    def test_inputgen_rejects_invalid_schema(self, tmp_path, monkeypatch):
        """Malformed inputgen config must fail closed (nonzero exit)."""
        cfg = tmp_path / "bad.json"
        cfg.write_text(json.dumps({"signals": ["clk"], "cycles": 10}))
        monkeypatch.setattr(sys, "argv", ["inputgen", str(cfg)])
        with pytest.raises(SystemExit) as exc:
            inputgen_main()
        assert exc.value.code not in (0, None)
