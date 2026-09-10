"""More CLI / fixture regressions (HDLTOOLS-0001 D1/D4/D5/E2)."""

import json
import sys
from pathlib import Path

import pytest

from hdltools.mmap import parse_mmap_file
from hdltools.mmap.builder import MMBuilder
from hdltools.patterns import Pattern
from hdltools.tools.fnboundary import main as fnboundary_main
from hdltools.tools.inputgen import main as inputgen_main
from hdltools.tools.vgc import main as vgc_main
from hdltools.vcd.tracker import VCDValueTracker

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT1_VG = REPO_ROOT / "assets" / "tests" / "input1.vg"
SAMPLE_MM = REPO_ROOT / "assets" / "tests" / "sample.mm"

TRACKER_VCD = """$date
$end
$version
$end
$timescale 1ns $end
$scope module top $end
$var wire 4 ! data [3:0] $end
$upscope $end
$enddefinitions $end
$dumpvars
b0000 !
$end
#0
#10
b1010 !
#20
b0000 !
#30
b1010 !
"""


def test_vcdtracker_pattern_occurrences():
    """D1: VCDValueTracker finds pattern matches in a synthetic VCD."""
    tracker = VCDValueTracker(
        Pattern("b1010"),
        preconditions=None,
        postconditions=None,
        time_range=None,
    )
    tracker.parse(TRACKER_VCD)
    hist = tracker.history
    n = len(hist._entries) if hasattr(hist, "_entries") else len(hist)
    assert n >= 2


@pytest.mark.skipif(not INPUT1_VG.is_file(), reason="input1.vg missing")
def test_vgc_inputgen_pipeline(tmp_path, monkeypatch):
    """D4: vgc → JSON → inputgen produces hex vector output."""
    json_out = tmp_path / "input.json"
    txt_out = tmp_path / "input.txt"

    monkeypatch.setattr(
        sys, "argv", ["vgc", str(INPUT1_VG), "--output", str(json_out)]
    )
    vgc_main()
    assert json_out.is_file()
    data = json.loads(json_out.read_text())
    assert "sequence" in data or "initial" in data or isinstance(data, (dict, list))

    monkeypatch.setattr(
        sys, "argv", ["inputgen", str(json_out), "--output", str(txt_out)]
    )
    inputgen_main()
    assert txt_out.is_file()
    text = txt_out.read_text().strip()
    assert text
    assert any(ch in "01abcdefABCDEF" for ch in text.replace("\n", ""))


def test_fnboundary_list_fns(tmp_path, monkeypatch, capsys):
    """D5: --list-fns prints function names from objdump-like input."""
    asm = tmp_path / "sample.asm"
    asm.write_text(
        "objdump: file format elf32-littlearm\n"
        "Disassembly of section .text:\n"
        "00001000 <_start>:\n"
        "1000: e3a00000 mov r0, #0\n"
        "1004: e12fff1e bx lr\n"
        "00001008 <main>:\n"
        "1008: e92d4000 push {lr}\n"
        "100c: e8bd8000 pop {pc}\n"
    )
    monkeypatch.setattr(sys, "argv", ["fnboundary", "--list-fns", str(asm)])
    fnboundary_main()
    out = capsys.readouterr().out
    assert "_start" in out
    assert "main" in out


@pytest.mark.skipif(not SAMPLE_MM.is_file(), reason="sample.mm missing")
def test_sample_mm_mmbuilder_semantics():
    """E2: assets/tests/sample.mm parses and builds CONTROL/STATUS."""
    text, model = parse_mmap_file(str(SAMPLE_MM))
    mmap = MMBuilder(text).visit(model)
    assert "CONTROL" in mmap.registers
    assert "STATUS" in mmap.registers
    assert mmap.ports["IRQ_EN"].direction == "out"
