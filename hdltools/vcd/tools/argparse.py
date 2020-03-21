"""Common ArgumentParser patterns."""

from argparse import ArgumentParser
from hdltools.vcd.trigger import VCDTriggerDescriptor


class ArgumentParserPattern:
    """Argument parser pattern."""

    def __init__(self, arg_name, **kwargs):
        """Initialize."""
        if not isinstance(arg_name, str):
            raise TypeError("argument name must be a string")
        self._name = arg_name
        self._kwargs = kwargs

    @property
    def arg_name(self):
        """Get argument name."""
        return self._arg_name

    @property
    def kwargs(self):
        """Get kwargs."""
        return self._kwargs

    def add_to_argparser(self, parser):
        """Add this pattern to an ArgumentParser."""
        if not isinstance(parser, ArgumentParser):
            raise TypeError("parser must be an ArgumentParser object")

    def parse_args(self, args):
        """Parse arguments."""
        raise NotImplementedError


class RestrictTimePattern(ArgumentParserPattern):
    """Simulation time restriction pattern."""

    def __init__(self):
        """Initialize."""
        super().__init__(
            "--restrict-time",
            help="restrict tracking to simulation time range",
        )

    def parse_args(self, args):
        """Parse."""
        if getattr(args, self.arg_name) is not None:
            restrict_time = getattr(args, self.arg_name).split(",")
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
            return (start, end)


class PreconditionPattern(ArgumentParserPattern):
    """Precondition pattern."""

    def __init__(self):
        """Initialize."""
        super().__init__(
            "--precondition",
            help="wait for a series of pre-conditions before tracking starts",
            nargs="+",
        )

    def parse_args(self, args):
        """Parse."""
        if args.precondition is not None:
            return [
                VCDTriggerDescriptor.from_str(precondition)
                for precondition in args.precondition
            ]


class PostconditionPattern(ArgumentParserPattern):
    """Postcondition pattern."""

    def __init__(self):
        """Initialize."""
        super().__init__(
            "--postcondition",
            help="stop tracking after pre-conditions are met, under postconditions",
            nargs="+",
        )

    def parse_args(self, args):
        """Parse."""
        if args.postcondition is not None:
            return [
                VCDTriggerDescriptor.from_str(postcondition)
                for postcondition in args.postcondition
            ]


ARG_RESTRICT_TIME = RestrictTimePattern()
ARG_PRECONDITION = PreconditionPattern()
ARG_POSTCONDITION = PostconditionPattern()
