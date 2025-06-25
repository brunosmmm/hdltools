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


def parse_vcd_timescale(timescale_str):
    """Parse VCD timescale string and return (value, unit)."""
    if not timescale_str:
        return 1, 'ns'  # Default fallback
    
    # Remove common whitespace and normalize
    timescale_str = timescale_str.strip()
    
    # Extract number and unit
    import re
    match = re.match(r'(\d+)\s*(\w+)', timescale_str)
    if match:
        value = int(match.group(1))
        unit = match.group(2).lower()
        return value, unit
    
    # Fallback defaults
    return 1, 'ns'


def convert_time_units(time_value, from_scale_value, from_scale_unit, to_unit):
    """Convert time from VCD units to display units."""
    
    # Time scale conversion factors to seconds
    time_scales = {
        'fs': 1e-15,
        'ps': 1e-12,
        'ns': 1e-9,
        'us': 1e-6,
        'ms': 1e-3,
        's': 1
    }
    
    if from_scale_unit not in time_scales or to_unit not in time_scales:
        return time_value  # Return unchanged if unknown units
    
    # Convert to seconds first
    time_in_seconds = time_value * from_scale_value * time_scales[from_scale_unit]
    
    # Convert to target unit
    converted_time = time_in_seconds / time_scales[to_unit]
    
    return converted_time


def format_time_value(value, unit):
    """Format time value with appropriate precision."""
    if value == int(value):
        return f"{int(value)}"
    elif value < 0.001:
        return f"{value:.6f}"
    elif value < 1:
        return f"{value:.3f}"
    else:
        return f"{value:.2f}"


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
    parser.add_argument(
        "--time-units", 
        help="Display time units for cycles (default: ns)", 
        choices=["fs", "ps", "ns", "us", "ms", "s"], 
        default="ns"
    )
    parser.add_argument(
        "--show-events", 
        help="Print all event occurrences with timing details", 
        action="store_true"
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
    try:
        if maybe_vcd:
            evt_tracker.parse(vcddata)
        else:
            with open(args.vcd, "rb") as data:
                evt_tracker.parse(data)
    except RuntimeError as e:
        if "Cannot locate VCD variable" in str(e):
            print(f"ERROR: {e}")
            print("\nThe signal name in your configuration may be incorrect.")
            print("Use vcdhier tool to explore the VCD file hierarchy and find the correct signal name.")
            exit(1)
        else:
            raise

    output = {
        "counts": evt_tracker.event_counts,
        "cycles": evt_tracker.event_cycles,
        "history": [evt.serialized for evt in evt_tracker.event_history],
    }

    if args.output is not None:
        with open(args.output, "w") as outfile:
            json.dump(output, outfile, indent=2)

    if args.dump_counts:
        # Get VCD timescale for unit conversion
        timescale_raw = getattr(evt_tracker, 'timescale', None)
        
        # Fallback: extract timescale from VCD file directly if parser doesn't have it
        if timescale_raw is None:
            try:
                with open(args.vcd, 'r') as vcd_file:
                    for line_num, line in enumerate(vcd_file):
                        if line_num > 50:  # Timescale should be in VCD header
                            break
                        if line.strip().startswith('$timescale'):
                            if '$end' in line:
                                # Single line format: $timescale 1fs $end
                                parts = line.split()
                                if len(parts) >= 2:
                                    timescale_raw = parts[1]
                            else:
                                # Multi-line format - timescale value on next line
                                next_line = next(vcd_file, '').strip()
                                if next_line and not next_line.startswith('$'):
                                    timescale_raw = next_line
                            break
            except:
                pass  # Continue with fallback if file reading fails
        
        # Final fallback to reasonable default
        if timescale_raw is None:
            timescale_raw = "1 ns"
        
        vcd_scale_value, vcd_scale_unit = parse_vcd_timescale(timescale_raw)
        
        # Print header with time units
        time_unit_header = f"TIME ({args.time_units})"
        print("{:<20}{:>10}{:>15}".format("EVENT", "COUNT", time_unit_header))
        
        for evt_name in evt_tracker.event_counts:
            count = output["counts"][evt_name]
            cycles = output["cycles"][evt_name]
            
            # Convert time units
            converted_time = convert_time_units(cycles, vcd_scale_value, vcd_scale_unit, args.time_units)
            formatted_time = format_time_value(converted_time, args.time_units)
            
            print("{:<20}{:>10}{:>15}".format(evt_name, count, formatted_time))
    
    if args.show_events:
        # Get VCD timescale for unit conversion (reuse from above)
        if 'vcd_scale_value' not in locals():
            timescale_raw = getattr(evt_tracker, 'timescale', None)
            if timescale_raw is None:
                try:
                    with open(args.vcd, 'r') as vcd_file:
                        for line_num, line in enumerate(vcd_file):
                            if line_num > 50:
                                break
                            if line.strip().startswith('$timescale'):
                                if '$end' in line:
                                    parts = line.split()
                                    if len(parts) >= 2:
                                        timescale_raw = parts[1]
                                else:
                                    next_line = next(vcd_file, '').strip()
                                    if next_line and not next_line.startswith('$'):
                                        timescale_raw = next_line
                                break
                except:
                    pass
            if timescale_raw is None:
                timescale_raw = "1 ns"
            vcd_scale_value, vcd_scale_unit = parse_vcd_timescale(timescale_raw)
        
        print("\nEvent Occurrences:")
        print("{:<20}{:<15}{:<15}{:<15}{:<12}".format("EVENT", "START", "END", "DURATION", "UUID"))
        print("-" * 80)
        
        for evt in evt_tracker.event_history:
            # Convert times to display units
            start_time = convert_time_units(evt.time, vcd_scale_value, vcd_scale_unit, args.time_units)
            end_time = convert_time_units(evt.time + evt.duration, vcd_scale_value, vcd_scale_unit, args.time_units)
            duration = convert_time_units(evt.duration, vcd_scale_value, vcd_scale_unit, args.time_units)
            
            # Format times appropriately
            start_str = format_time_value(start_time, args.time_units)
            end_str = format_time_value(end_time, args.time_units)
            duration_str = format_time_value(duration, args.time_units)
            
            # Truncate UUID for display
            uuid_short = str(evt.uuid)[:8] + "..."
            
            print("{:<20}{:<15}{:<15}{:<15}{:<12}".format(
                evt.evt_type, 
                f"{start_str} {args.time_units}",
                f"{end_str} {args.time_units}",
                f"{duration_str} {args.time_units}",
                uuid_short
            ))


if __name__ == "__main__":
    main()
