"""VCD tracker debug."""

from argparse import ArgumentParser
from hdltools.vcd import VCDScope
from hdltools.vcd.tracker import VCDValueTracker
from hdltools.patterns import Pattern
from hdltools.vcd.trigger import VCDTriggerDescriptor, VCDTriggerError


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
    signal_lists = parser.add_mutually_exclusive_group()
    signal_lists.add_argument(
        "--ignore-sig",
        help="ignore signals by regular expression matching",
        nargs="+",
    )
    # TODO: implement
    signal_lists.add_argument(
        "--restrict-sig",
        help="restrict to signal names by regular expression matching",
        nargs="+",
    )
    parser.add_argument(
        "--ignore-scope",
        help="ignore scopes by regular expression matching",
        nargs="+",
    )
    parser.add_argument(
        "--src-anchor", help="anchor source to signal name by regex match"
    )
    parser.add_argument(
        "--dest-anchor",
        help="anchor destination to signal name by regex match",
    )
    parser.add_argument(
        "--precondition",
        help="wait for a series of pre-conditions before tracking starts",
        nargs="+",
    )
    parser.add_argument(
        "--postcondition",
        help="stop tracking after pre-conditions are met, under postconditions",
        nargs="+",
    )
    parser.add_argument(
        "--restrict-time", help="restrict tracking to simulation time range"
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

    preconditions = None
    if args.precondition is not None:
        try:
            preconditions = [
                VCDTriggerDescriptor.from_str(precondition)
                for precondition in args.precondition
            ]
        except VCDTriggerError:
            print("ERROR: precondition is malformed")
            exit(1)

    postconditions = None
    if args.postcondition is not None:
        if args.precondition is None:
            print(
                "WARNING: specifying postconditions without preconditions has no effect"
            )
        try:
            postconditions = [
                VCDTriggerDescriptor.from_str(postcondition)
                for postcondition in args.postcondition
            ]
        except VCDTriggerError:
            print("ERROR: postcondition is malformed")
            exit(1)

    restrict_src, inclusive_src = (
        VCDScope.from_str(restrict_src) if restrict_src is not None else (None, False)
    )

    restrict_dest, inclusive_dest = (
        VCDScope.from_str(restrict_dest) if restrict_dest is not None else (None, False)
    )

    if args.restrict_time is not None:
        restrict_time = args.restrict_time.split(",")
        if len(restrict_time) != 2:
            print("ERROR: invalid time range specification")
            exit(1)
        start, end = restrict_time
        try:
            start = int(start)
            end = int(end)
        except ValueError:
            print("ERROR: invalid values in time range specification")
            exit(1)
        restrict_time = (start, end)
    else:
        restrict_time = None

    tracker = VCDValueTracker(
        Pattern(args.pattern),
        restrict_src=restrict_src,
        restrict_dest=restrict_dest,
        inclusive_src=inclusive_src,
        inclusive_dest=inclusive_dest,
        ignore_signals=args.ignore_sig,
        ignore_scopes=args.ignore_scope,
        anchors=(args.src_anchor, args.dest_anchor),
        preconditions=preconditions,
        postconditions=postconditions,
        time_range=restrict_time,
    )
    tracker.parse(vcddata)

    if args.dump_hier:
        tracker.scope_hier.dump()

    # print(tracker.history)
    origin = None
    arrival = None
    print("INFO: {} occurrences".format(len(tracker.history)))
    if tracker.maybe_src is not None:
        print(
            "INFO: probable source is {}".format(
                tracker.history[tracker.maybe_src]
            )
        )
        origin = tracker.history[tracker.maybe_src].time
    if tracker.maybe_dest is not None:
        print(
            "INFO: probable destination is {}".format(
                tracker.history[tracker.maybe_dest]
            )
        )
        arrival = tracker.history[tracker.maybe_dest].time
        if origin is not None:
            print(
                "INFO: probable travel time was {} cycles".format(
                    arrival - origin
                )
            )
