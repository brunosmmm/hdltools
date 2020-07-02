"""Input generation."""

from dictator.config import validate_config
from dictator.validators.base import validate_string
from dictator.validators.lists import ValidateChoice, SubListValidator
from dictator.validators.maps import SubDictValidator
from dictator.validators.integer import positive_integer
from dictator.validators.dependency import KeyDependencyMap

EVENT_TYPES = ("initial", "set", "clear", "toggle")
_EVENT_DEPS = {
    "initial": ("value",),
    "set": ("mask",),
    "clear": ("mask",),
    "toggle": ("mask",),
}


@validate_string
@ValidateChoice(*EVENT_TYPES)
@KeyDependencyMap(**_EVENT_DEPS)
def _validate_evt_type(evt_type, **kwargs):
    """Validate event type."""
    return evt_type


@validate_string
@ValidateChoice("abs", "rel")
def _validate_time_mode(mode, **kwargs):
    """Validate time mode."""
    return mode


@SubDictValidator(
    {"mode": _validate_time_mode},
    {"delta": positive_integer, "time": positive_integer},
)
def _validate_time(time, **kwargs):
    """Validate time."""
    return time


EVENT_REQ = {"event": _validate_evt_type}
EVENT_OPT = {"mask": int, "time": _validate_time, "value": positive_integer}


@SubListValidator(EVENT_REQ, EVENT_OPT)
def _validate_sequence(seq_data, **kwargs):
    """Validate sequence."""
    return seq_data


INPUT_REQ = {"sequence": _validate_sequence}
INPUT_OPT = {"vector_size": positive_integer}


def validate_input_config(input_config):
    """Validate input configuration."""
    return validate_config(input_config, INPUT_REQ, INPUT_OPT)
