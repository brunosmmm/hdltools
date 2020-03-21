"""Common ArgumentParser patterns."""

from argparse import ArgumentParser


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


ARG_RESTRICT_TIME = RestrictTimePattern()
