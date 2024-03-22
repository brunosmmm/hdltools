"""Common functionality for mmap tools."""

from argparse import ArgumentParser


class MmapError(Exception):
    """Base class for mmap errors."""


def add_param_replace_args(parser: ArgumentParser):
    """Add arguments for parameter replacement."""
    parser.add_argument(
        "--param-replace",
        type=str,
        nargs="+",
        help="Replace parameters in the form key=value",
    )


def parse_param_replace_args(args):
    """Parse parameter replacement arguments."""
    param_replacements = {}
    if args.param_replace is not None:
        for replacement in args.param_replace:
            try:
                param, value = replacement.split("=")
                value = int(value)
            except (IndexError, ValueError) as ex:
                raise MmapError(
                    f"Invalid parameter replacement: {replacement}"
                ) from ex
            param_replacements[param] = value
    return param_replacements
