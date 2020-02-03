"""Signal pattern matching."""

import re
from typing import Union


class PatternError(Exception):
    """Pattern error."""


class Pattern:
    """Signal pattern representation."""

    PATTERN_REGEX = re.compile(r"[01xX]+")
    PATTERN_REGEX_BYTES = re.compile(b"[01xX]+")

    def __init__(self, pattern: Union[str, bytes]):
        """Initialize."""
        if not isinstance(pattern, (str, bytes)):
            raise TypeError("pattern must be a string or bytes")
        if isinstance(pattern, str):
            m = self.PATTERN_REGEX.match(pattern)
        else:
            m = self.PATTERN_REGEX_BYTES.match(pattern)
        if m is None:
            raise PatternError("pattern is invalid")

        self._pattern = pattern

    @property
    def pattern(self):
        """Get pattern."""
        return self._pattern

    def __len__(self):
        """Get length."""
        return len(self._pattern)

    def match(self, value: Union[str, bytes]) -> bool:
        """Match against value."""
        if not isinstance(value, (str, bytes)):
            raise TypeError("value must be string or bytes")

        if type(value) != type(self._pattern):
            raise TypeError("incompatible types for value and pattern")

        pattern = self._pattern
        if len(value) < len(self._pattern):
            # zero-extend incomin value
            count = len(self._pattern) - len(value)
            value = "0" * count + value
        elif len(value) > len(self._pattern):
            # zero-extend pattern
            count = len(value) - len(self._pattern)
            pattern = "0" * count + self._pattern
        for value_bit, expected_bit in zip(value, pattern):
            if expected_bit in ("x", "X"):
                # don't care
                continue
            if expected_bit != value_bit:
                return False

        return True
