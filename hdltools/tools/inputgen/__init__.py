#!/usr/bin/env python3
"""Generate input vector."""

from argparse import ArgumentParser
import json
import sys

from dictator.errors import ConfigurationError
from hdltools.vecgen.inputcfg import validate_input_config

DEFAULT_VECTOR_SIZE = 32


def fatal_error(msg):
    """Fatal error."""
    print(f"FATAL: {msg}")
    exit(1)


def main():
    parser = ArgumentParser()
    parser.add_argument("config", help="event file")
    parser.add_argument("--output", help="output", default="input.txt")

    args = parser.parse_args()

    try:
        if args.config == "-":
            config = json.loads(sys.stdin.read())
        else:
            with open(args.config, "r") as cfg:
                config = json.load(cfg)
        config = validate_input_config(config)
    except OSError:
        print("ERROR: cannot open configuration file")
        exit(1)
    except json.JSONDecodeError:
        print("ERROR: json decode error")
        exit(1)
    except ConfigurationError as ex:
        print(f"ERROR: configuration error: '{ex}'")
        exit(1)

    # generate input vectors
    sequence = config["sequence"]
    vector_size = config.get("vector_size", DEFAULT_VECTOR_SIZE)
    current_state = 0
    current_time = 0
    generated_vectors = []
    for idx, evt in enumerate(sequence):
        event = evt["event"]
        if idx == 0 and event != "initial":
            fatal_error("first event must be of initial type")
        if event == "initial":
            if idx > 0:
                fatal_error("initial event must be first in sequence")
            current_state = evt["value"]
            generated_vectors.append(current_state)
            current_time += 1
        else:
            time = evt["time"]
            if time["mode"] == "rel":
                tdelta = time["delta"] - 1
                # insert copies of current state
                for _ in range(tdelta):
                    generated_vectors.append(current_state)
                    current_time += 1
            else:
                tdelta = time["time"] - current_time
                if tdelta < 0:
                    fatal_error(
                        f"in event {idx}: absolute time is in the past"
                    )

                for _ in range(tdelta):
                    generated_vectors.append(current_state)
                    current_time += 1
            if event == "set":
                current_state |= evt["mask"]
            elif event == "clear":
                current_state &= ~evt["mask"]
            elif event == "toggle":
                current_state ^= evt["mask"]
            else:
                # cannot happen
                fatal_error("unknown error")

            generated_vectors.append(current_state)
            current_time += 1

    # dump
    try:
        with open(args.output, "w") as outf:
            outf.writelines(
                [hex(value)[2:] + "\n" for value in generated_vectors]
            )
    except OSError:
        fatal_error("cannot write output file")


if __name__ == "__main__":
    main()
