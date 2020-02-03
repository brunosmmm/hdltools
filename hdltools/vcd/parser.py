"""VCD parser."""

from scoff.parsers.token import SimpleTokenField
from scoff.parsers.generic import DataParser
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
    EXTENTS,
)


SCOPE_PARSER = LineMatcher(
    r"\$scope",
    SEP,
    SimpleTokenField("stype", SCOPE_TYPE),
    SEP,
    SimpleTokenField("sname", SCOPE_NAME),
    SEP,
    DIRECTIVE_TERM,
)

UPSCOPE_PARSER = LineMatcher(r"\$upscope", SEP, DIRECTIVE_TERM)

VAR_PARSER = LineMatcher(
    r"\$var",
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
    r"\$enddefinitions", SEP, DIRECTIVE_TERM, change_state="dump"
)

GENERIC_PARSER = LineMatcher(
    SimpleTokenField("dtype", r"\$(\w+)"),
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

SIM_TIME_PARSER = LineMatcher(SimpleTokenField("time", SIM_TIME))

DUMPVARS_PARSER = LineMatcher(r"\$dumpvars", push_state="initial")
END_PARSER = LineMatcher(r"\$end", pop_state=1)

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
    SIM_TIME_PARSER,
    DUMPVARS_PARSER,
]


class BaseVCDParser(DataParser):
    """Simple VCD parser."""

    def __init__(self):
        """Initialize."""
        super().__init__("header")
        self._ticks = 0

    @property
    def current_time(self):
        """Get current time."""
        return self._ticks

    def header_statement_handler(self, stmt, fields):
        """Handle header stateent."""

    def initial_value_handler(self, stmt, fields):
        """Handle initial value assignment."""

    def value_change_handler(self, stmt, fields):
        """Handle value change."""

    def clock_change_handler(self, time):
        """Handle clock change."""

    def _advance_clock(self, ticks):
        """Advance wall clock."""
        self.clock_change_handler(ticks)
        self._ticks = ticks

    def _state_header(self, data):
        """Parse."""
        size, stmt, fields = self._try_parse(VCD_DEFINITION_LINES, data)
        self.header_statement_handler(stmt, fields)
        return size

    def _state_initial(self, data):
        size, stmt, fields = self._try_parse(VCD_VAR_LINES + [END_PARSER], data)
        if stmt != END_PARSER:
            self.initial_value_handler(stmt, fields)
        return size

    def _state_dump(self, data):
        size, stmt, fields = self._try_parse(VCD_VAR_LINES, data)
        if stmt == SIM_TIME_PARSER:
            self._advance_clock(fields["time"])
        elif stmt != DUMPVARS_PARSER:
            self.value_change_handler(stmt, fields)
        return size
