"""CLI regressions for vcdcmp / mmap_docgen (HDLTOOLS-0001 D2/D3)."""

import sys
from pathlib import Path

import pytest

from hdltools.tools.mmap_docgen import main as docgen_main
from hdltools.tools.vcdcmp import main as vcdcmp_main

REPO_ROOT = Path(__file__).resolve().parents[1]
VIDEOCHK = REPO_ROOT / "assets" / "tests" / "videochk.mmap"

MINI_VCD = """$date
$end
$version
$end
$timescale 1ns $end
$scope module top $end
$var wire 1 ! clk $end
$upscope $end
$enddefinitions $end
$dumpvars
0!
$end
#0
#10
1!
#20
0!
"""


def test_vcdcmp_identical_files_equivalent(tmp_path, monkeypatch, capsys):
    """D2: identical VCDs → exit 0 and EQUIVALENT."""
    f1 = tmp_path / "a.vcd"
    f2 = tmp_path / "b.vcd"
    f1.write_text(MINI_VCD)
    f2.write_text(MINI_VCD)
    monkeypatch.setattr(sys, "argv", ["vcdcmp", str(f1), str(f2), "-q"])

    with pytest.raises(SystemExit) as exc:
        vcdcmp_main()

    assert exc.value.code == 0
    assert "EQUIVALENT" in capsys.readouterr().out


def test_vcdcmp_missing_file_exits_nonzero(tmp_path, monkeypatch):
    """D2: missing file → exit 1."""
    f1 = tmp_path / "a.vcd"
    f1.write_text(MINI_VCD)
    monkeypatch.setattr(sys, "argv", ["vcdcmp", str(f1), str(tmp_path / "missing.vcd")])

    with pytest.raises(SystemExit) as exc:
        vcdcmp_main()

    assert exc.value.code == 1


@pytest.mark.skipif(not VIDEOCHK.is_file(), reason="assets/tests/videochk.mmap missing")
def test_mmap_docgen_videochk_content(monkeypatch, capsys):
    """D3: docgen prints CONTROL/FSIZE tables for videochk.mmap."""
    monkeypatch.setattr(sys, "argv", ["mmap_docgen", str(VIDEOCHK)])
    docgen_main()
    out = capsys.readouterr().out
    assert "CONTROL" in out
    assert "FSIZE" in out
