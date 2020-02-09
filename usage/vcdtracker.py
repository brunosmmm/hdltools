"""VCD tracker debug."""

from argparse import ArgumentParser
from hdltools.vcd import VCDScope
from hdltools.vcd.tracker import VCDValueTracker
from hdltools.patterns import Pattern


if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("vcd", help="path to vcd file")
    parser.add_argument("pattern", help="pattern to search for")
    parser.add_argument(
        "--dump-hier", action="store_true", help="dump hierarchy"
    )
    parser.add_argument("--restrict-src", help="restrict source scope")
    parser.add_argument("--restrict-dest", help="restrict destination scope")

    args = parser.parse_args()

    with open(args.vcd, "r") as data:
        vcddata = data.read()

    restrict_src = (
        VCDScope.from_str(args.restrict_src)
        if args.restrict_src is not None
        else None
    )

    restrict_dest = (
        VCDScope.from_str(args.restrict_dest)
        if args.restrict_dest is not None
        else None
    )

    tracker = VCDValueTracker(
        Pattern(args.pattern),
        restrict_src=restrict_src,
        restrict_dest=restrict_dest,
    )
    tracker.parse(vcddata)

    if args.dump_hier:
        tracker.scope_hier.dump()

    # print(tracker.history)
    print("INFO: {} occurrences".format(len(tracker.history)))
