"""Signal pattern matching."""

import re


class PatternError(Exception):
    """Pattern error."""


class Pattern:
    """Signal pattern representation."""

    PATTERN_REGEX = re.compile(r"[01xX]+")

    def __init__(self, pattern: str):
        """Initialize."""
        if not isinstance(pattern, str):
            raise TypeError("pattern must be a string")
        m = self.PATTERN_REGEX.match(pattern)
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

    def match(self, value: str) -> bool:
        """Match against value."""
        if not isinstance(value, str):
            raise TypeError("value must be string")
        if len(value) != len(self._pattern):
            raise ValueError("cannot compare, different lengths")
        for value_bit, expected_bit in zip(value, self._pattern):
            if expected_bit in ("x", "X"):
                # don't care
                continue
            if expected_bit != value_bit:
                return False

        return True
