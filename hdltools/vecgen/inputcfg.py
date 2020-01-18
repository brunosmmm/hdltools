"""Input generation."""

from dictator.config import validate_config

from dictator.validators import validate_string, ValidateChoice

from dictator.util import (
    AutoValidateList,
    KeyDependencyMap,
    AutoValidateDict,
    default_validate_int,
    default_validate_pos_int,
)

EVENT_TYPES = ("initial", "set", "clear", "toggle")
_EVENT_DEPS = {
    "initial": ("value",),
    "set": ("mask",),
    "clear": ("mask",),
    "toggle": ("mask",),
}


@validate_string
@ValidateChoice(EVENT_TYPES)
@KeyDependencyMap(**_EVENT_DEPS)
def _validate_evt_type(evt_type, **kwargs):
    """Validate event type."""
    return evt_type


@validate_string
@ValidateChoice(("abs", "rel"))
def _validate_time_mode(mode, **kwargs):
    """Validate time mode."""
    return mode


@AutoValidateDict(
    {"mode": _validate_time_mode},
    {"delta": default_validate_pos_int, "time": default_validate_pos_int},
)
def _validate_time(time, **kwargs):
    """Validate time."""
    return time


EVENT_REQ = {"event": _validate_evt_type}
EVENT_OPT = {
    "mask": default_validate_int,
    "time": _validate_time,
    "value": default_validate_pos_int,
}


@AutoValidateList(EVENT_REQ, EVENT_OPT)
def _validate_sequence(seq_data, **kwargs):
    """Validate sequence."""
    return seq_data


INPUT_REQ = {"sequence": _validate_sequence}
INPUT_OPT = {"vector_size": default_validate_pos_int}


def validate_input_config(input_config):
    """Validate input configuration."""
    return validate_config(input_config, INPUT_REQ, INPUT_OPT)
