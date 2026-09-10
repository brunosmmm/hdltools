"""Promoted debug-script scenario: hierarchical value match (HDLTOOLS-0001 C6)."""

from hdltools.tools.vcdevts import VCDEventTrackerWithHierarchy
from hdltools.vcd.trigger.trigcond import build_descriptors_from_str

# Minimal stand-in for root debug_vcd_value_matching / cpu_scope scripts:
# nested scopes + bus with known value at a known time.
CPU_SCOPE_VCD = """$date
$end
$version
$end
$timescale 1ns $end
$scope module test_bench $end
$scope module cpu $end
$var wire 1 ! clk $end
$var wire 16 " inst_addr [15:0] $end
$upscope $end
$upscope $end
$enddefinitions $end
$dumpvars
0!
b0000000000000000 "
$end
#0
#10
1!
#20
0!
b0000000000110000 "
#30
1!
b0000000000110000 "
"""


def test_cpu_scope_inst_addr_match_from_debug_scenario():
    """C6: scoped bus pattern match that debug scripts used to validate manually."""
    desc = build_descriptors_from_str("test_bench::cpu::inst_addr[15:0]==0x0030")[0][0]
    events = {"hit_addr": (([desc], "&&"), {})}
    tracker = VCDEventTrackerWithHierarchy(
        events=events,
        postconditions=None,
        preconditions=None,
        time_range=None,
        debug=False,
    )
    tracker.parse(CPU_SCOPE_VCD)

    cond = next(iter(list(tracker._evt_triggers.values())[0][0].global_sensitivity_list))
    assert cond.vcd_var == '"'

    hits = [e for e in tracker.event_history if e.evt_type == "hit_addr"]
    assert len(hits) == 1
    assert hits[0].time == 20
