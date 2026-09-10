"""VCD value resolution regressions (HDLTOOLS-0001 Wave C)."""

from hdltools.vcd.efficient_storage import BinarySignalValue, EfficientVCDStorage
from hdltools.vcd.streaming_parser import StreamingVCDParser

MINI_VCD = """$date
    today
$end
$version
    Test VCD
$end
$timescale
    1ns
$end
$scope module top $end
$var wire 1 a clk $end
$var wire 4 b counter [3:0] $end
$upscope $end
$enddefinitions $end
$dumpvars
0a
b0000 b
$end
#0
#10
1a
#20
0a
b0001 b
#30
1a
b1010 b
#40
0a
"""


def test_binary_signal_value_from_vcd_string():
    """C2: BinarySignalValue parses b-prefix and pads to width."""
    val = BinarySignalValue(4, "b1010")
    assert val.to_string().replace("b", "")[-4:] == "1010"


def test_efficient_storage_value_at_time():
    """C2: EfficientVCDStorage returns correct value via time index."""
    store = EfficientVCDStorage()
    store.add_variable("b", "counter", "wire", 4, ["top"])
    store.set_value("b", 0, "b0000")
    store.set_value("b", 20, "b0001")
    store.set_value("b", 30, "b1010")

    assert store.get_value("b", 10).to_string().endswith("0000")
    assert store.get_value("b", 20).to_string().endswith("0001")
    assert store.get_value("b", 25).to_string().endswith("0001")
    assert store.get_value("b", 30).to_string().endswith("1010")


def test_streaming_parser_value_at_time_golden():
    """C1: StreamingVCDParser exposes known values at known times."""
    parser = StreamingVCDParser()
    parser.parse(MINI_VCD)

    # Scalar clock
    assert parser.get_value_at_time_efficient("a", 0) in ("0", "0a", "b0")
    clk10 = parser.get_value_at_time_efficient("a", 10)
    assert clk10 is not None
    assert "1" in clk10

    # Vector counter
    c20 = parser.get_value_at_time_efficient("b", 20)
    c30 = parser.get_value_at_time_efficient("b", 30)
    assert c20 is not None and "0001" in c20.replace(" ", "")
    assert c30 is not None and "1010" in c30.replace(" ", "")
