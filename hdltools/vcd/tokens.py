"""VCD Tokens."""

SEP = b"\s+"
SEP_OPT = b"\s*"
INTEGER = b"([0-9]+)"
STRING = b"([^$]+)"
DIRECTIVE_TERM = b"\$end"
VAR_ID = b"([^\s]+)"
NAME = b"([\w\(\)]+)"
SCOPE_NAME = b"([\w\[\]]+)"
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
EXTENTS = b"(\[[0-9]+\s*:\s*[0-9]+\])?"
# REAL_NUMBER = b"[rR](" + SIG_VALUE + r"+)"
