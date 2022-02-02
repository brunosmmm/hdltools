"""Entity generators."""

from typing import Dict, Type, Tuple, Any
from argparse import ArgumentParser


class HDLEntityGeneratorError(Exception):
    """Entity generation error."""


class HDLEntityGenerator:
    """Entity generator.

    Provides minimal introspection into a parameterizeable entity
    that can be generated using hdltools.
    """

    REQUIRED_PARAMETERS: Dict[str, Tuple[str, Type, Any]] = {}
    OPTIONAL_PARAMETERS: Dict[str, Tuple[str, Type]] = {}

    @classmethod
    def _generate_entity(cls, params, backend=None):
        """Generate entity."""
        raise NotImplementedError

    @classmethod
    def generate_entity(cls, params, backend=None):
        """Generate entity."""
        if not isinstance(params, dict):
            raise TypeError("params must be a dictionary")
        for param_name, param_desc in cls.REQUIRED_PARAMETERS.items():
            if param_name not in params:
                raise HDLEntityGeneratorError(
                    f"required parameter '{param_name}' not present"
                )
            _, param_type, _ = param_desc
            if not isinstance(params[param_name], param_type):
                raise HDLEntityGeneratorError(
                    f"invalid type for parameter '{param_name}'"
                )

        return cls._generate_entity(params, backend)

    @classmethod
    def get_commandline_parser(cls):
        """Get command line parser."""
        parser = ArgumentParser()
        for param_name, param_desc in cls.REQUIRED_PARAMETERS.items():
            param_help, param_type, param_default = param_desc
            parser.add_argument(
                param_name,
                help=param_help,
                type=param_type,
                default=param_default,
            )
        for param_name, param_desc in cls.OPTIONAL_PARAMETERS.items():
            param_help, param_type = param_desc
            parser.add_argument(
                f"--{param_name}", help=param_help, type=param_type
            )

        return parser

    @classmethod
    def parse_commandline(cls):
        """Parse commandline directly."""
        parser = cls.get_commandline_parser()
        args = parser.parse_args()

        params = {
            param_name: param_value
            for param_name, param_value in vars(args).items()
            if param_value is not None
        }
        return params

    @classmethod
    def parse_and_generate(cls, backend=None):
        """Parse command line and generate."""
        params = cls.parse_commandline()
        return cls.generate_entity(params, backend)
