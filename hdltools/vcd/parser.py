"""VCD parser."""

import io
import pickle
from scoff.parsers.token import SimpleTokenField
from scoff.parsers.generic import DataParser, ParserError
from scoff.parsers.linematch import LineMatcher
from hdltools.vcd.tokens import (
    SEP,
    SEP_OPT,
    SCOPE_TYPE,
    SCOPE_NAME,
    NAME,
    DIRECTIVE_TERM,
    VAR_TYPE,
    VAR_ID,
    INTEGER,
    STRING,
    SIM_TIME,
    SIG_VALUE,
    BINARY_NUMBER,
    REAL_NUMBER,
    EXTENTS,
)
from hdltools.vcd.variable import VCDVariable
from hdltools import HDLToolsError


class VCDParserError(HDLToolsError):
    """VCD Parser error."""


SCOPE_PARSER = LineMatcher(
    rb"\$scope",
    SEP,
    SimpleTokenField("stype", SCOPE_TYPE),
    SEP,
    SimpleTokenField("sname", SCOPE_NAME),
    SEP,
    DIRECTIVE_TERM,
)

UPSCOPE_PARSER = LineMatcher(rb"\$upscope", SEP, DIRECTIVE_TERM)

VAR_PARSER = LineMatcher(
    rb"\$var",
    SEP,
    SimpleTokenField("vtype", VAR_TYPE),
    SEP,
    SimpleTokenField("width", INTEGER),
    SEP,
    SimpleTokenField("id", VAR_ID),
    SEP,
    SimpleTokenField("name", NAME),
    SEP,
    SimpleTokenField("extents", EXTENTS),
    SEP_OPT,
    DIRECTIVE_TERM,
)

END_DEFS_PARSER = LineMatcher(
    rb"\$enddefinitions", SEP, DIRECTIVE_TERM, change_state="dump"
)

GENERIC_PARSER = LineMatcher(
    SimpleTokenField("dtype", rb"\$(\w+)"),
    SEP,
    SimpleTokenField("body", STRING),
    SEP,
    DIRECTIVE_TERM,
)

SCALAR_VALUE_CHANGE_PARSER = LineMatcher(
    SimpleTokenField("value", SIG_VALUE),
    SEP_OPT,
    SimpleTokenField("var", VAR_ID),
)

VECTOR_VALUE_CHANGE_PARSER = LineMatcher(
    SimpleTokenField("value", BINARY_NUMBER),
    SEP,
    SimpleTokenField("var", VAR_ID),
)

REAL_VALUE_CHANGE_PARSER = LineMatcher(
    SimpleTokenField("value", REAL_NUMBER),
    SEP_OPT,
    SimpleTokenField("var", VAR_ID),
)

SIM_TIME_PARSER = LineMatcher(SimpleTokenField("time", SIM_TIME))

DUMPVARS_PARSER = LineMatcher(rb"\$dumpvars", push_state="initial")
END_PARSER = LineMatcher(rb"\$end", pop_state=1)

VCD_DEFINITION_LINES = [
    SCOPE_PARSER,
    UPSCOPE_PARSER,
    VAR_PARSER,
    END_DEFS_PARSER,
    GENERIC_PARSER,
]

VCD_VAR_LINES = [
    SCALAR_VALUE_CHANGE_PARSER,
    VECTOR_VALUE_CHANGE_PARSER,
    REAL_VALUE_CHANGE_PARSER,
    SIM_TIME_PARSER,
    DUMPVARS_PARSER,
]


# Legacy BaseVCDParser has been replaced by StreamingVCDParser
# Backward compatibility is provided by the lazy loader below


class _RestrictedUnpickler(pickle.Unpickler):
    """Unpickler that only allows safe built-in types."""

    _SAFE_BUILTINS = frozenset({"str", "int", "float", "dict", "list", "tuple", "bool", "set"})

    def find_class(self, module, name):
        """Only allow safe builtins."""
        if module == "builtins" and name in self._SAFE_BUILTINS:
            return getattr(__builtins__ if isinstance(__builtins__, dict) else type(__builtins__), name, None) or __import__(module).__dict__[name]
        raise pickle.UnpicklingError(
            f"forbidden unpickle: {module}.{name}"
        )


def restricted_pickle_load(data):
    """Load pickle data using restricted unpickler (safe types only)."""
    if isinstance(data, (bytes, bytearray)):
        data = io.BytesIO(data)
    return _RestrictedUnpickler(data).load()


class CompiledVCDParser:
    """Compiled vcd parser."""

    def __init__(self, *args, **kwargs):
        """Initialize."""
        # FIXME: placeholder
        self._state_hooks = {}
        super().__init__(*args, **kwargs)
        if "debug" in kwargs:
            self._debug = kwargs["debug"]
        else:
            self._debug = False
        self._ticks = 0
        self._old_ticks = 0
        self._vars = {}

    @property
    def current_time(self):
        """Get current time."""
        return self._ticks

    @property
    def last_cycle_time(self):
        """Get last simulation cycle time."""
        return self._old_ticks

    @property
    def variables(self):
        """Get variables."""
        return self._vars

    @property
    def states(self):
        """Get states."""
        return ["header", "initial", "dump"]

    def header_statement_handler(self, stmt, fields):
        """Handle header statement."""

    def initial_value_handler(self, stmt, fields):
        """Handle initial value assignment."""

    def value_change_handler(self, stmt, fields):
        """Handle value change."""

    def clock_change_handler(self, time):
        """Handle clock change."""
        print(f"DEBUG: @{time}")

    # FIXME: hooks do NOT work yet
    def add_state_hook(self, state, hook):
        """Add state hook."""
        if not callable(hook):
            raise TypeError("hook must be callable")
        if state not in self.states:
            raise ParserError(f"unknown state '{state}'")
        if state not in self._state_hooks:
            self._state_hooks[state] = {hook}
        else:
            self._state_hooks[state] |= {hook}

    def _dump_state(self, fields):
        """Emulate dump state."""
        for hook in self._state_hooks["dump"]:
            hook("dump", None, fields)

        self.value_change_handler({}, fields)

    def _state_change_handler(self, old_state, new_state):
        """State change handler."""

    def _advance_clock(self, ticks):
        """Advance wall clock."""
        self.clock_change_handler(ticks)
        self._old_ticks = self._ticks
        self._ticks = ticks

    def parse(self, data):
        """Parse."""
        header = restricted_pickle_load(data)
        if header != "DUMP_START":
            raise RuntimeError("invalid dump")
        vars_done = False
        while True:
            val = restricted_pickle_load(data)
            if isinstance(val, dict) and vars_done is False:
                var = VCDVariable.unpack(val)
                self._vars[var.identifiers[0]] = var
            elif isinstance(val, dict):
                time = val["time"]
                states = val["states"]
                for varid, state in states.items():
                    fields = {"var": varid, "value": bin(state)}
                    self._dump_state(fields)
                self._advance_clock(time)
            elif isinstance(val, str):
                if val == "VARS_END":
                    vars_done = True
                    self._state_change_handler("header", "dump")
                elif val == "DUMP_END":
                    break
                else:
                    raise RuntimeError("unknown value in dump")

# Backward compatibility - simple lazy import to avoid circular imports
# BaseVCDParser is now just an alias that's set at first access

_streaming_parser_class = None

def _get_streaming_parser_class():
    """Get the StreamingVCDParser class, cached."""
    global _streaming_parser_class
    if _streaming_parser_class is None:
        from .streaming_parser import StreamingVCDParser
        _streaming_parser_class = StreamingVCDParser
    return _streaming_parser_class

# Simple module-level __getattr__ for lazy loading
def __getattr__(name):
    """Module-level getattr for lazy loading of BaseVCDParser."""
    if name == 'BaseVCDParser':
        return _get_streaming_parser_class()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
