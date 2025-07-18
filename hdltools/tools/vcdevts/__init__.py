#!/usr/bin/env python3
"""VCD Event tracker."""

import pickle
import json
import re
import os
from argparse import ArgumentParser

from dictator.config import validate_config
from dictator.validators.replace import AutoFragmentReplace
from dictator.validators.lists import SubListValidator
from dictator.validators.integer import validate_positive_integer
from dictator.validators.maps import SubDictValidator

from hdltools.vcd.event import VCDEventTrackerLegacy, VCDEventTrackerCompiled, get_tracker_class
from hdltools.vcd.streaming_parser import StreamingVCDParser
from hdltools.vcd.mixins.hierarchy import VCDHierarchyAnalysisMixin

# Create hierarchy-enabled VCD event tracker for handling scoped signals
class VCDParserWithHierarchy(StreamingVCDParser, VCDHierarchyAnalysisMixin):
    """VCD parser with hierarchy support for scoped signal resolution."""
    
    def variable_search(self, name: str, scope=None, aliases: bool = True):
        """Use hierarchy mixin's variable search instead of StreamingVCDParser's."""
        # Delegate to hierarchy mixin which handles VCDScope objects properly
        return VCDHierarchyAnalysisMixin.variable_search(self, name, scope, aliases)

VCDEventTrackerWithHierarchy = get_tracker_class(VCDParserWithHierarchy)
from hdltools.vcd.trigger.trigcond import build_descriptors_from_str
from hdltools.binutils.tools.boundary import fn_boundary
from hdltools.vcd.trigger import VCDTriggerDescriptor
from hdltools.vcd.tools.argparse import (
    ARG_RESTRICT_TIME,
    ARG_PRECONDITION,
    ARG_POSTCONDITION,
)


DEBUG = bool(os.environ.get("DEBUG"))


# validator hacks
class CallFragmentReplacer(AutoFragmentReplace):
    """Replace and call."""

    CALL_PATTERN = re.compile(r"#([\w]+)\(([^#\(\)]+)\)")
    SUBROUTINES = {"fnBoundaryStart": "_fn_boundary_start"}

    def _try_call(self, routine_name, *args):
        """Try to call subroutine."""
        if routine_name not in self.SUBROUTINES:
            raise RuntimeError(f"unknown subroutine {routine_name}")
        function = getattr(self, self.SUBROUTINES[routine_name])
        return function(*args)

    def _fn_boundary_start(self, binary, fn_name):
        """Function boundary."""
        if binary == "":
            print(
                "ERROR: this configuration requires the use of the --simulated-binary argument"
            )
            exit(1)
        with open(binary, "r") as asmdump:
            dump = asmdump.read()
        start, _ = fn_boundary(dump, fn_name)
        return bin(start)

    def validate(self, _value, **kwargs):
        """Validate."""
        ret = super().validate(_value, **kwargs)
        m = self.CALL_PATTERN.match(ret)
        if m is not None:
            return self._try_call(
                m.group(1), *[s.strip() for s in m.group(2).split(",")]
            )
        return ret


def validate_values(value, **kwargs):
    """Validate values."""
    validator = CallFragmentReplacer()
    updated_values = {
        key: validator.validate(val, **kwargs) for key, val in value.items()
    }
    return updated_values


SIM_OPT = {
    "precondition": AutoFragmentReplace(),
    "postcondition": AutoFragmentReplace(),
}
EVT_REQ = {"name": str, "conds": AutoFragmentReplace()}
EVT_OPT = {"timeout": validate_positive_integer}
EVT_CFG_REQ = {"events": SubListValidator(EVT_REQ, EVT_OPT)}
EVT_CFG_OPT = {
    "simulation": SubDictValidator(optional_keys=SIM_OPT),
    "values": validate_values,
}


def main():
    parser = ArgumentParser()

    parser.add_argument("evt_def", help="Path to event definition file")
    parser.add_argument("vcd", help="Path to VCD file")
    parser.add_argument(
        "--dump-counts", help="Print event counts", action="store_true"
    )
    parser.add_argument("--output", help="Output file")
    parser.add_argument(
        "--simulated-binary",
        help="Simulated binary for static co-analysis",
        default="",
    )
    parser.add_argument(
        "--set-config-value",
        action="append",
        help="Set key,value pair in event definition file",
    )
    parser.add_argument(
        "--append-config-value",
        action="append",
        help="Append value to a configuration key",
    )
    ARG_RESTRICT_TIME.add_to_argparser(parser)
    ARG_PRECONDITION.add_to_argparser(parser)
    ARG_POSTCONDITION.add_to_argparser(parser)

    args = parser.parse_args()
    restrict_time = ARG_RESTRICT_TIME.parse_args(args)
    preconditions = ARG_PRECONDITION.parse_args(args)
    postconditions = ARG_POSTCONDITION.parse_args(args)

    try:
        with open(args.evt_def, "r") as evt_cfg_contents:
            evt_cfg = json.load(evt_cfg_contents)

    except json.JSONDecodeError:
        print("ERROR: malformed json in configuration file")
        exit(1)
    except OSError as ex:
        print(f"ERROR: could not open file: {ex}")
        exit(1)

    if args.simulated_binary != "":
        if not os.path.exists(args.simulated_binary):
            print(
                f"ERROR: simulated binary not found: {args.simulated_binary}"
            )
            exit(1)

    maybe_vcd = False
    with open(args.vcd, "rb") as data:
        try:
            tracker_class = VCDEventTrackerCompiled
            header = pickle.load(data)
            if header != "DUMP_START":
                print("ERROR: invalid dump")
                exit(1)
        except pickle.UnpicklingError:
            # maybe is vcd file
            maybe_vcd = True

    if maybe_vcd:
        tracker_class = VCDEventTrackerWithHierarchy
        with open(args.vcd, "r") as data:
            vcddata = data.read()

    if args.append_config_value:
        for configval in args.append_config_value:
            try:
                key, value = configval.split(",")
            except ValueError:
                print("ERROR: in --append-config-value: malformed argument")
                exit(1)

            if key.strip() not in evt_cfg:
                print(
                    "ERROR: in --append-config-value: key not in configuration"
                )
                exit(1)

            evt_cfg[key.strip()] += value.strip()

    extra_config = {}
    if args.set_config_value:
        for configval in args.set_config_value:
            try:
                key, value = configval.split(",")
            except ValueError:
                print("ERROR: in --set-config-value: malformed argument")
                exit(1)

            extra_config[key.strip()] = value.strip()

    # parse configuration file
    parsed_cfg = validate_config(
        evt_cfg,
        EVT_CFG_REQ,
        EVT_CFG_OPT,
        gobble_unknown=False,
        binary=args.simulated_binary,
        **extra_config,
    )

    # add postconditions and preconditions in configuration file
    if "simulation" in parsed_cfg:
        if "postcondition" in parsed_cfg["simulation"]:
            cfg_postcondition = VCDTriggerDescriptor.from_str(
                parsed_cfg["simulation"]["postcondition"]
            )
            if postconditions is None:
                postconditions = [cfg_postcondition]
            else:
                postconditions.append(cfg_postcondition)

    if "simulation" in parsed_cfg:
        if "precondition" in parsed_cfg["simulation"]:
            cfg_precondition = VCDTriggerDescriptor.from_str(
                parsed_cfg["simulation"]["precondition"]
            )
            if preconditions is None:
                preconditions = [cfg_precondition]
            else:
                preconditions.append(cfg_precondition)

    events = {}
    for event in parsed_cfg["events"]:
        name = event.pop("name")
        cond_str = event.pop("conds")
        try:
            cond = build_descriptors_from_str(cond_str)
            events[name] = (cond, event)
        except Exception as e:
            print(f"Error in event '{name}':")
            print(f"Condition: '{cond_str}'")
            print(f"{e}")
            print()
            exit(1)

    evt_tracker = tracker_class(
        events=events,
        postconditions=postconditions,
        preconditions=preconditions,
        time_range=restrict_time,
        debug=DEBUG,
    )
    if maybe_vcd:
        evt_tracker.parse(vcddata)
    else:
        with open(args.vcd, "rb") as data:
            evt_tracker.parse(data)

    output = {
        "counts": evt_tracker.event_counts,
        "cycles": evt_tracker.event_cycles,
        "history": [evt.serialized for evt in evt_tracker.event_history],
    }

    if args.output is not None:
        with open(args.output, "w") as outfile:
            json.dump(output, outfile, indent=2)

    if args.dump_counts:
        print("{:<20}{:>10}{:>10}".format("EVENT", "COUNT", "CYCLES"))
        for evt_name in evt_tracker.event_counts:
            count = output["counts"][evt_name]
            cycles = output["cycles"][evt_name]
            print("{:<20}{:>10}{:>10}".format(evt_name, count, cycles))


if __name__ == "__main__":
    main()
