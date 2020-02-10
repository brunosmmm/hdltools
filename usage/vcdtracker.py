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
    restrict_group = parser.add_mutually_exclusive_group()
    restrict_group.add_argument(
        "--restrict-endpoints", help="restrict source/destination scopes"
    )
    restrict_group.add_argument(
        "--restrict-scope", help="restrict to single scope"
    )
    parser.add_argument(
        "--ignore-sig",
        help="ignore signals by regular expression matching",
        nargs="+",
    )
    parser.add_argument(
        "--ignore-scope",
        help="ignore scopes by regular expression matching",
        nargs="+",
    )

    args = parser.parse_args()

    with open(args.vcd, "r") as data:
        vcddata = data.read()

    restrict_src = None
    restrict_dest = None
    if args.restrict_endpoints is not None:
        try:
            restrict_src, restrict_dest = args.restrict_endpoints.split(",")
        except ValueError:
            print(
                "ERROR: --restrict-endpoints takes two arguments separated by a comma"
            )
            exit(1)

    inclusive_src = (
        True
        if restrict_src is not None and restrict_src.endswith("::")
        else False
    )

    inclusive_dest = (
        True
        if restrict_dest is not None and restrict_dest.endswith("::")
        else False
    )

    restrict_src = (
        VCDScope.from_str(restrict_src) if restrict_src is not None else None
    )

    restrict_dest = (
        VCDScope.from_str(restrict_dest) if restrict_dest is not None else None
    )

    tracker = VCDValueTracker(
        Pattern(args.pattern),
        restrict_src=restrict_src,
        restrict_dest=restrict_dest,
        inclusive_src=inclusive_src,
        inclusive_dest=inclusive_dest,
        ignore_signals=args.ignore_sig,
        ignore_scopes=args.ignore_scope,
    )
    tracker.parse(vcddata)

    if args.dump_hier:
        tracker.scope_hier.dump()

    # print(tracker.history)
    print("INFO: {} occurrences".format(len(tracker.history)))
