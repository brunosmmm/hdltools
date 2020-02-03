"""VCD tracker debug."""

from argparse import ArgumentParser
from hdltools.vcd.tracker import VCDValueTracker
from hdltools.patterns import Pattern


if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("vcd")
    parser.add_argument("--dump-hier", action="store_true")

    args = parser.parse_args()

    with open(args.vcd, "r") as data:
        vcddata = data.read()

    tracker = VCDValueTracker(Pattern("1010"))
    tracker.parse(vcddata)

    if args.dump_hier:
        tracker.scope_hier.dump()
