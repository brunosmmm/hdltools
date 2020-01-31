"""VCD Tokens."""

SEP = r"\s+"
SEP_OPT = r"\s*"
INTEGER = r"([0-9]+)"
STRING = r"([^$]+)"
DIRECTIVE_TERM = r"\$end"
VAR_ID = r"([^\s]+)"
NAME = r"(\w+)"
VCD_SCOPE_TYPES = ["begin", "fork", "module", "function", "task"]
SCOPE_TYPE = r"(" + r"|".join(VCD_SCOPE_TYPES) + r")"
VCD_VAR_TYPES = [
    "event",
    "integer",
    "parameter",
    "real",
    "realtime",
    "reg",
    "supply0",
    "supply1",
    "time",
    "tri",
    "triand",
    "trior",
    "trireg",
    "tri0",
    "tri1",
    "wand",
    "wire",
    "wor",
    "string",
]
VAR_TYPE = r"(" + r"|".join(VCD_VAR_TYPES) + r")"
SIM_TIME = r"#([0-9]+)"
SIG_VALUE = r"[01xXzZ]"
BINARY_NUMBER = r"[bB](" + SIG_VALUE + r"+)"
# REAL_NUMBER = r"[rR](" + SIG_VALUE + r"+)"
