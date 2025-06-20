"""VCD Tokens."""

SEP = rb"\s+"
SEP_OPT = rb"\s*"
INTEGER = b"([0-9]+)"
STRING = b"([^$]+)"
DIRECTIVE_TERM = rb"\$end"
VAR_ID = rb"([^\s]+)"
NAME = rb"([\w\(\)]+)"
SCOPE_NAME = rb"([\w\[\]]+)"
VCD_SCOPE_TYPES = [b"begin", b"fork", b"module", b"function", b"task"]
SCOPE_TYPE = b"(" + b"|".join(VCD_SCOPE_TYPES) + b")"
VCD_VAR_TYPES = [
    b"event",
    b"integer",
    b"parameter",
    b"real",
    b"realtime",
    b"reg",
    b"supply0",
    b"supply1",
    b"time",
    b"tri",
    b"triand",
    b"triob",
    b"trireg",
    b"tri0",
    b"tri1",
    b"wand",
    b"wire",
    b"wor",
    b"string",
]
VAR_TYPE = b"(" + b"|".join(VCD_VAR_TYPES) + b")"
SIM_TIME = b"#([0-9]+)"
_SIG_VALUE = b"[01xXzZ]"
SIG_VALUE = b"(" + _SIG_VALUE + b")"
BINARY_NUMBER = b"[bB](" + _SIG_VALUE + b"+)"
EXTENTS = rb"(\[[0-9]+\s*:\s*[0-9]+\])?"
REAL_NUMBER = rb"[rR]([+-]?[0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?)"
