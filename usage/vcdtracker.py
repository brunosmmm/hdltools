"""VCD tracker debug."""

from hdltools.vcd.tracker import VCDValueTracker
from hdltools.patterns import Pattern

if __name__ == "__main__":

    with open("tests/assets/example.vcd", "r") as data:
        vcddata = data.read()

    tracker = VCDValueTracker(Pattern("1010"))
    tracker.parse(vcddata)

    tracker.scope_hier.dump()
