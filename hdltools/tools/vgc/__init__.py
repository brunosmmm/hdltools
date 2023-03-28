#!/usr/bin/env python3
"""Test vecgen."""

import os
import json
from argparse import ArgumentParser
from hdltools.vecgen import parse_vecgen_file


def main():
    parser = ArgumentParser()
    parser.add_argument("input", help="input filename")
    cmd_group = parser.add_mutually_exclusive_group()
    cmd_group.add_argument("--output", help="output filename")
    cmd_group.add_argument(
        "--dump", help="dump to stdout", action="store_true"
    )

    args = parser.parse_args()

    ret = parse_vecgen_file(args.input)

    if args.dump is False:
        if args.output is None:
            base_fname, _ = os.path.splitext(os.path.basename(args.input))
            output_fname = base_fname + ".json"
        else:
            output_fname = args.output

        try:
            with open(output_fname, "w") as outf:
                json.dump(ret, outf)

        except OSError:
            print("cannot write output file")
            exit(1)
    else:
        print(json.dumps(ret, indent=2))


if __name__ == "__main__":
    main()
