"""Hierarchical VCD event / linking regressions (HDLTOOLS-0001 C3/C4)."""

from hdltools.tools.vcdevts import VCDEventTrackerWithHierarchy
from hdltools.vcd.trigger.trigcond import build_descriptors_from_str

HIER_VCD = """$date
    today
$end
$version
    Test VCD
$end
$timescale
    1ns
$end
$scope module tb $end
$scope module cpu $end
$var wire 1 ! clk $end
$var wire 4 " state [3:0] $end
$upscope $end
$upscope $end
$enddefinitions $end
$dumpvars
0!
b0000 "
$end
#0
#10
1!
#20
0!
b0001 "
#30
1!
b0010 "
#40
0!
b0010 "
#50
1!
b0010 "
"""


def test_hierarchy_parser_links_scoped_bus_condition():
    """C3: scoped bus descriptor with [msb:lsb] resolves to VCD var id."""
    desc = build_descriptors_from_str("tb::cpu::state[3:0]==2")[0][0]
    events = {"state_two": (([desc], "&&"), {})}
    tracker = VCDEventTrackerWithHierarchy(
        events=events,
        postconditions=None,
        preconditions=None,
        time_range=None,
        debug=False,
    )
    tracker.parse(HIER_VCD)

    condtable = list(tracker._evt_triggers.values())[0][0]
    cond = next(iter(condtable.global_sensitivity_list))
    assert cond.vcd_var is not None
    assert cond.vcd_var == '"'


def test_hierarchy_event_counts_exact():
    """C4: hierarchical tracker records clock edges and state matches."""
    clk_desc = build_descriptors_from_str("tb::cpu::clk==1")[0][0]
    state_desc = build_descriptors_from_str("tb::cpu::state[3:0]==2")[0][0]
    events = {
        "clock_high": (([clk_desc], "&&"), {}),
        "state_two": (([state_desc], "&&"), {}),
    }
    tracker = VCDEventTrackerWithHierarchy(
        events=events,
        postconditions=None,
        preconditions=None,
        time_range=None,
        debug=False,
    )
    tracker.parse(HIER_VCD)

    # Clock highs that return low before EOF complete and are counted
    assert tracker.event_counts.get("clock_high", 0) == 2

    # Sustained state match may not end → assert history starts
    state_starts = [e for e in tracker.event_history if e.evt_type == "state_two"]
    assert len(state_starts) >= 1
    assert state_starts[0].time == 30
