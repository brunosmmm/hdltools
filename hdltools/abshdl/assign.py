"""Assignment."""

from . import HDLObject
from .const import HDLIntegerConstant
from .expr import HDLExpression
from .signal import HDLSignal, HDLSignalSlice
from .concat import HDLConcatenation
from .stmt import HDLStatement
from .port import HDLModulePort
from .ifelse import HDLIfExp
from .macro import HDLMacroValue


class HDLLazyValue(HDLObject):
    """Lazy evaluated value."""

    def __init__(self, fn, *args, **kwargs):
        """Initialize."""
        self._args = kwargs.pop("fnargs", [])
        self._kwargs = kwargs.pop("fnkwargs", {})
        self._fn = fn

    def evaluate(self, signals=None, symbols=None):
        """Evaluate."""
        if signals is None:
            signals = {}
        if symbols is None:
            symbols = {}
        if not callable(self._fn):
            if self._fn not in symbols or not callable(symbols[self._fn]):
                raise RuntimeError(
                    "unresolved lazy function: '{}'".format(self._fn)
                )
            else:
                self._fn = symbols[self._fn]

        resolved_args = []
        for arg in self._args:
            if isinstance(arg, str) and arg in signals:
                resolved_args.append(signals[arg])
            elif isinstance(arg, HDLObject):
                resolved_args.append(arg)
            else:
                raise RuntimeError(
                    "unresolved argument in lazy eval: '{}'".format(arg)
                )

        resolved_kwargs = {}
        for name, kwarg in self._kwargs.items():
            if isinstance(kwarg, str) and arg in signals:
                resolved_kwargs[name] = signals[kwarg]
            elif isinstance(arg, HDLObject):
                resolved_args[name] = kwarg
            else:
                raise RuntimeError(
                    "unresolved argument in lazy eval: '{}'".format(kwarg)
                )

        return self._fn(*resolved_args, **resolved_kwargs)


class HDLAssignment(HDLStatement):
    """Signal assignment."""

    def __init__(self, signal, value, assign_type="block", **kwargs):
        """Initialize."""
        if isinstance(signal, HDLModulePort):
            if signal.direction in ("out", "inout"):
                signal = signal.signal
            else:
                raise ValueError("cannot assign to input port")

        if not isinstance(signal, (HDLSignal, HDLSignalSlice)):
            raise TypeError("only HDLSignal, HDLSignalSlice can be assigned")

        self.assign_type = assign_type
        self.signal = signal

        if isinstance(signal, HDLSignal):
            sig_type = signal.sig_type
        elif isinstance(signal, HDLSignalSlice):
            sig_type = signal.signal.sig_type

        if sig_type in ("comb", "const"):
            stmt_type = "par"
        elif sig_type in ("reg", "var"):
            stmt_type = "seq"
        elif sig_type == "other":
            stmt_type = "null"

        if isinstance(
            value,
            (
                HDLIntegerConstant,
                HDLSignal,
                HDLExpression,
                HDLSignalSlice,
                HDLConcatenation,
                HDLIfExp,
                HDLMacroValue,
                HDLLazyValue,
            ),
        ):
            self.value = value
        elif isinstance(value, int):
            self.value = HDLIntegerConstant(value, **kwargs)
        else:
            raise TypeError(
                "only integer, HDLIntegerConstant, "
                "HDLSignal, HDLExpression, HDLConcatenation, "
                "HDLIfExp, HDLMacroValue "
                "allowed, got: {}".format(value.__class__.__name__)
            )

        super().__init__(stmt_type=stmt_type)

    def get_assignment_type(self):
        """Get assignment type."""
        if isinstance(self.signal, HDLSignal):
            sig_type = self.signal.sig_type
        elif isinstance(self.signal, HDLSignalSlice):
            sig_type = self.signal.signal.sig_type

        if sig_type in ("comb", "const"):
            return "parallel"
        else:
            return "series"

    def dumps(self):
        """Get representation."""
        ret_str = self.signal.dumps(decl=False)
        if self.signal.sig_type in ("comb", "const"):
            ret_str += " = "
        else:
            ret_str += " <= "
        ret_str += self.value.dumps() + ";"

        return ret_str

    def is_legal(self):
        """Determine legality."""
        # always return True for now.
        return True
