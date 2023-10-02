"""Builtin functions."""

import math

from hdltools.abshdl import HDLObject
from hdltools.abshdl.expr import HDLExpression


class HDLBuiltinFunction(HDLObject):
    """Builtin function."""

    def __init__(self, name, args, ret, cb):
        """Initialize.

        Args
        ----
        name: str
           Function name
        args: List
           Argument List: TBD
        ret: class
           Return type ? TBD
        """
        self.name = name
        self.arg_list = args
        self.ret_type = ret
        self.cb = cb
        super().__init__()

    def call(self, *args, **kwargs):
        """Perform function call.

        Args
        ----
        args: list
           Argument list
        """
        # perform argument checking?
        return self.cb(*args, **kwargs)


class HDLBuiltins(HDLObject):
    """Default builtin objects."""

    # placeholders
    _functions = {
        "_ceil": HDLBuiltinFunction(
            "ceil",
            [],
            None,
            lambda x, **scope: int(
                math.ceil(HDLBuiltins._decide_and_evaluate(x, **scope))
            ),
        ),
        "_log2": HDLBuiltinFunction(
            "log2",
            [],
            None,
            lambda x, **scope: math.log2(
                HDLBuiltins._decide_and_evaluate(x, **scope)
            ),
        ),
        "_clog2": HDLBuiltinFunction(
            "clog2",
            [],
            None,
            lambda x, **scope: int(
                math.ceil(
                    math.log2(HDLBuiltins._decide_and_evaluate(x, **scope))
                )
            ),
        ),
    }

    @staticmethod
    def _decide_and_evaluate(value, **scope):
        if isinstance(value, int):
            return value
        if isinstance(value, HDLExpression):
            return value.evaluate(**scope)
        raise TypeError('invalid type: "{}"'.format(type(value)))

    @classmethod
    def get_builtin_scope(cls):
        """Get dictionary with all available symbols."""
        scope = {}
        scope.update(cls._functions)
        return scope
