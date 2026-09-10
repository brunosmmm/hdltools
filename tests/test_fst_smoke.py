"""FST conversion smoke (HDLTOOLS-0001 E5 / IDEA-467).

Must reject magic-only stubs (FST\\x00\\xff ≈ 5 bytes, 0 variables). The prior
smoke only checked st_size > 0 and skipped on any exception — confirmatory.
"""

from pathlib import Path

import pytest

from hdltools.fst import FSTFormat
from hdltools.fst.converter import convert_vcd_to_fst

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


def test_convert_vcd_to_fst_writes_variables(tmp_path):
    """E5: VCD→FST must record at least one variable, not a magic+EOF stub."""
    vcd = tmp_path / "mini.vcd"
    fst = tmp_path / "mini.fst"
    vcd.write_text(MINI_VCD)

    convert_vcd_to_fst(str(vcd), str(fst))

    assert fst.is_file()
    data = fst.read_bytes()
    assert data.startswith(FSTFormat.MAGIC)
    # Magic (4) + end marker (1) is the empty stub the broken converter wrote.
    stub_size = len(FSTFormat.MAGIC) + 1
    assert len(data) > stub_size, (
        f"FST output is magic-only stub ({len(data)} bytes); no hierarchy/VC data"
    )
    # Hierarchy block type must appear if variables were written
    assert bytes([FSTFormat.BLOCK_HEADER]) in data or bytes(
        [FSTFormat.BLOCK_HIER]
    ) in data


def test_convert_vcd_to_fst_includes_zero_valued_initial(tmp_path, capsys):
    """Regression: value '0' must not be dropped by truthiness checks."""
    vcd = tmp_path / "mini.vcd"
    fst = tmp_path / "mini.fst"
    vcd.write_text(MINI_VCD)

    convert_vcd_to_fst(str(vcd), str(fst))
    captured = capsys.readouterr().out
    assert "Variables: 0" not in captured
    assert "Wrote 1 variables" in captured or "Variables: 1" in captured
