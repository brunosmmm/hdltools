"""Signal pattern matching."""

import re
from typing import Union

from hdltools import HDLToolsError


class PatternError(HDLToolsError):
    """Pattern error."""


class Pattern:
    """Signal pattern representation."""

    PATTERN_REGEX = re.compile(r"[01xX]+")
    PATTERN_REGEX_BYTES = re.compile(b"[01xX]+")

    def __init__(self, pattern: Union[str, bytes, int]):
        """Initialize with automatic format detection and conversion."""
        if not isinstance(pattern, (str, bytes, int)):
            raise TypeError("pattern must be a string, bytes, or integer")

        original_pattern = pattern
        
        # Handle integer inputs
        if isinstance(pattern, int):
            if pattern < 0:
                raise PatternError(f"Pattern cannot be negative: {pattern}")
            self._pattern = bin(pattern)[2:]  # Remove '0b' prefix
            return
        
        # Handle string/bytes inputs with format detection
        if isinstance(pattern, str):
            pattern = pattern.strip()
            if not pattern:
                raise PatternError("Pattern cannot be empty. Use binary digits (0, 1, x, X).")
            
            # Try to detect and convert different formats
            try:
                converted_pattern = self._detect_and_convert_format(pattern)
            except Exception as e:
                error_msg = self._generate_helpful_error_message(original_pattern, str(e))
                raise PatternError(error_msg) from e

            # Validate the converted pattern
            m = self.PATTERN_REGEX.fullmatch(converted_pattern)  # Use fullmatch to ensure entire pattern is valid
            if m is None:
                error_msg = self._generate_helpful_error_message(original_pattern)
                raise PatternError(error_msg)
                
            self._pattern = converted_pattern
        else:
            # bytes input
            m = self.PATTERN_REGEX_BYTES.fullmatch(pattern)  # Use fullmatch to ensure entire pattern is valid
            if m is None:
                error_msg = self._generate_helpful_error_message(original_pattern)
                raise PatternError(error_msg)
            self._pattern = pattern
    
    def _detect_and_convert_format(self, pattern: str) -> str:
        """Detect format and convert to binary representation."""
        original = pattern
        
        # Remove common prefixes/suffixes and detect format
        if pattern.startswith("0x") or pattern.startswith("0X"):
            # Hexadecimal with 0x prefix (REQUIRED for hex)
            hex_str = pattern[2:]
            if not hex_str:
                raise ValueError(f"Incomplete hexadecimal pattern '{pattern}' - missing digits after '0x'")
            return self._hex_to_bin(hex_str)
            
        elif pattern.startswith("0b") or pattern.startswith("0B"):
            # Binary with 0b prefix (REQUIRED for binary)
            binary_str = pattern[2:]
            if not binary_str:
                raise ValueError(f"Incomplete binary pattern '{pattern}' - missing digits after '0b'")
            # Normalize by removing leading zeros (but keep at least one digit)
            return binary_str.lstrip('0') or '0'
            
        elif pattern.endswith("h") or pattern.endswith("H"):
            # Hexadecimal with h suffix (legacy support, but discouraged)
            # Check this BEFORE the 'b' prefix to avoid conflict with "B9h" etc.
            hex_str = pattern[:-1]
            return self._hex_to_bin(hex_str)
            
        elif pattern.startswith("b") or pattern.startswith("B"):
            # Binary with b prefix (alternative binary format)
            binary_str = pattern[1:]
            if not binary_str:
                raise ValueError(f"Incomplete binary pattern '{pattern}' - missing digits after 'b'")
            # Normalize by removing leading zeros (but keep at least one digit)
            return binary_str.lstrip('0') or '0'
            
        elif pattern.isdigit():
            # Pure decimal number (no ambiguity - only digits 0-9)
            decimal_val = int(pattern)
            return bin(decimal_val)[2:]  # Remove '0b' prefix
            
        elif all(c in 'xX' for c in pattern):
            # Pure don't care patterns (contains only x, X)
            # This is allowed without prefix (e.g., "xxxx")
            return pattern
            
        else:
            # Invalid or ambiguous pattern
            # Generate helpful error message
            if any(c in 'ABCDEFabcdef' for c in pattern.replace('x', '').replace('X', '')):
                raise ValueError(f"Hexadecimal patterns must use '0x' prefix. Use '0x{pattern}' instead of '{pattern}'")
            elif any(c in '23456789' for c in pattern) and any(c in '01' for c in pattern):
                # Mixed digits that could be binary or decimal
                if len(pattern) > 1 and all(c in '01' for c in pattern):
                    raise ValueError(f"Binary patterns must use '0b' or 'b' prefix. Use '0b{pattern}' instead of '{pattern}'")
                else:
                    raise ValueError(f"Ambiguous pattern '{pattern}'. Use explicit format: '0x' for hex, '0b' for binary, or digits only for decimal")
            else:
                raise ValueError(f"Invalid pattern '{pattern}'. Use '0x' for hex, '0b' for binary, digits for decimal, or '01xX' for binary with don't care")
    
    def _hex_to_bin(self, hex_str: str) -> str:
        """Convert hexadecimal string to binary representation."""
        try:
            # Handle both upper and lower case
            hex_str = hex_str.upper()
            
            # Validate hex characters
            if not all(c in '0123456789ABCDEF' for c in hex_str):
                raise ValueError(f"Invalid hexadecimal characters in '{hex_str}'")
            
            # Convert to integer then to binary
            decimal_val = int(hex_str, 16)
            binary_str = bin(decimal_val)[2:]  # Remove '0b' prefix
            
            # Don't pad - let the result be minimal like decimal conversion
            return binary_str
            
        except ValueError as e:
            raise ValueError(f"Invalid hexadecimal pattern '{hex_str}': {e}") from e
    
    def _generate_helpful_error_message(self, pattern: Union[str, bytes, int], 
                                      conversion_error: str = None) -> str:
        """Generate a helpful error message for invalid patterns."""
        pattern_str = str(pattern)
        
        base_msg = f"Invalid pattern '{pattern}': "
        
        if conversion_error:
            base_msg += conversion_error + "\n"
        
        base_msg += "\nSupported pattern formats:\n"
        base_msg += "  • Binary: '1010', '101x', '0b1010' (digits: 0, 1, x, X)\n"
        base_msg += "  • Decimal: '15', '255' (any positive integer)\n"
        base_msg += "  • Hexadecimal: 'FFh', 'A3h', '0xFFFF' (with h suffix or 0x prefix)\n"
        base_msg += "\nExamples:\n"
        base_msg += "  Pattern('3') → '11' (decimal 3 to binary)\n"
        base_msg += "  Pattern('FFh') → '11111111' (hex FF to binary)\n"
        base_msg += "  Pattern('0x10') → '10000' (hex 10 to binary)\n"
        base_msg += "  Pattern('101x') → '101x' (binary with don't care)\n"
        
        return base_msg

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

    def is_numeric(self) -> bool:
        """Check if pattern represents a pure numeric value (no don't care bits)."""
        return all(c in '01' for c in self._pattern)

    def to_integer(self) -> int:
        """Convert pattern to integer value."""
        if not self.is_numeric():
            raise ValueError(f"Cannot convert pattern '{self._pattern}' with don't care bits to integer")
        return int(self._pattern, 2)  # Convert binary string to int

    def _clean_vcd_value(self, value: Union[str, bytes]) -> Union[str, bytes]:
        """Clean VCD value by removing common prefixes like 'b' and '0b'."""
        if isinstance(value, str):
            if value.startswith('0b') or value.startswith('0B'):
                return value[2:]
            elif value.startswith('b') or value.startswith('B'):
                return value[1:]
        return value
    
    def compare(self, value: Union[str, bytes], operator: str) -> bool:
        """Compare pattern against value using specified operator."""
        if operator in ('==', '!='):
            # Handle VCD prefixes for equality comparison
            clean_value = self._clean_vcd_value(value)
            result = self.match(clean_value)
            return result if operator == '==' else not result
        
        # Numerical comparison operators
        if not self.is_numeric():
            raise ValueError(f"Cannot use operator '{operator}' with pattern containing don't care bits")
        
        # Convert VCD value to integer (handle 'b' and '0b' prefixes)
        clean_value = self._clean_vcd_value(value)
            
        if not clean_value or not all(c in '01' for c in clean_value):
            raise ValueError(f"Cannot compare non-binary value '{value}' numerically")
        
        pattern_int = self.to_integer()
        try:
            value_int = int(clean_value, 2)
        except ValueError:
            raise ValueError(f"Cannot compare non-binary value '{value}' numerically")
        
        if operator == '>':
            return value_int > pattern_int
        elif operator == '<':
            return value_int < pattern_int
        elif operator == '>=':
            return value_int >= pattern_int
        elif operator == '<=':
            return value_int <= pattern_int
        else:
            raise ValueError(f"Unsupported operator: {operator}")

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
