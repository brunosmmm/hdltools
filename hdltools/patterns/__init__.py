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

        # tolerate some variations
        if isinstance(pattern, str):
            if pattern.endswith("h"):
                pattern = self.hex_to_bin(pattern)
            if pattern.startswith("0b"):
                pattern = pattern[2:]

            m = self.PATTERN_REGEX.match(pattern)
        elif isinstance(pattern, int):
            self._pattern = bin(pattern)
            return
        else:
            m = self.PATTERN_REGEX_BYTES.match(pattern)
        if m is None:
            raise PatternError(f"pattern is invalid: {pattern}")

        self._pattern = pattern

    @property
    def pattern(self):
        """Get pattern."""
        return self._pattern

    def __repr__(self):
        """Get representation."""
        return self.pattern

    def __len__(self):
        """Get length."""
        return len(self._pattern)

    def match(self, value: Union[str, bytes]) -> bool:
        """Match against value."""
        if value is None:
            # Handle None values (uninitialized signals) as no match
            return False
        if not isinstance(value, (str, bytes)):
            raise TypeError(
                f"value must be string or bytes, got {type(value)}"
            )

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

    @staticmethod
    def hex_to_bin(hexstr):
        """Convert hex to binary including don't cares."""
        if hexstr.endswith("h"):
            hexstr = hexstr[:-1]

        hexstr = hexstr.replace("x", "X")
        split = hexstr.split("X")
        ret = ""
        for fragment in split:
            ret += bin(int(fragment, 16)) if fragment else "xxxx"

        return ret
