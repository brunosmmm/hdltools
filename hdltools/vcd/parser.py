"""VCD parser."""

from collections import deque
from scoff.parsers.token import SimpleTokenField
from scoff.parsers.generic import DataParser, ParserError
from scoff.parsers.linematch import LineMatcher
from hdltools.vcd.tokens import (
    SEP,
    SEP_OPT,
    SCOPE_TYPE,
    NAME,
    DIRECTIVE_TERM,
    VAR_TYPE,
    VAR_ID,
    INTEGER,
    STRING,
    SIM_TIME,
    SIG_VALUE,
    BINARY_NUMBER,
)


SCOPE_PARSER = LineMatcher(
    r"\$scope",
    SEP,
    SimpleTokenField("stype", SCOPE_TYPE),
    SEP,
    SimpleTokenField("sname", NAME),
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
    DIRECTIVE_TERM,
)

END_DEFS_PARSER = LineMatcher(
    r"\$enddefinitions", SEP, DIRECTIVE_TERM, change_state="vars"
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


class VCDParser(DataParser):
    """Simple VCD parser."""

    def __init__(self):
        """Initialize."""
        super().__init__("header")
        self._state_stack = deque()
        self._state = "header"

    def _state_header(self, data):
        """Parse."""
        size, fields, stmt = self._try_parse(VCD_DEFINITION_LINES, data)
        return size

    def _state_initial(self, data):
        size, fields, stmt = self._try_parse(
            VCD_VAR_LINES + [END_PARSER], data
        )
        return size

    def _state_vars(self, data):
        size, fields, stmt = self._try_parse(VCD_VAR_LINES, data)
        return size
