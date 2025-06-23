"""Signal pattern matching."""

import re
from typing import Union


class PatternError(Exception):
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
                pattern = self._detect_and_convert_format(pattern)
            except Exception as e:
                error_msg = self._generate_helpful_error_message(original_pattern, str(e))
                raise PatternError(error_msg) from e

            m = self.PATTERN_REGEX.fullmatch(pattern)  # Use fullmatch to ensure entire pattern is valid
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
        if pattern.endswith("h") or pattern.endswith("H"):
            # Hexadecimal with suffix
            hex_str = pattern[:-1]
            return self._hex_to_bin(hex_str)
            
        elif pattern.startswith("0x") or pattern.startswith("0X"):
            # Hexadecimal with 0x prefix
            hex_str = pattern[2:]
            return self._hex_to_bin(hex_str)
            
        elif pattern.startswith("0b") or pattern.startswith("0B"):
            # Binary with 0b prefix
            return pattern[2:]
            
        elif all(c in '01xX' for c in pattern):
            # Binary format - contains only binary digits and don't care bits
            return pattern
            
        elif all(c in '0123456789ABCDEFabcdef' for c in pattern):
            # Could be hex or decimal - check for hex characteristics
            if any(c in 'ABCDEFabcdef' for c in pattern):
                # Contains hex letters - definitely hex
                return self._hex_to_bin(pattern)
            elif len(pattern) == 4 and any(c in '23456789' for c in pattern):
                # Length 4 with higher digits (common hex pattern like 1234, 8000)
                return self._hex_to_bin(pattern)
            else:
                # Pure digits - treat as decimal
                decimal_val = int(pattern)
                return bin(decimal_val)[2:]
                
        elif pattern.isdigit():
            # Pure decimal number
            decimal_val = int(pattern)
            return bin(decimal_val)[2:]  # Remove '0b' prefix
            
        else:
            # Mixed or invalid characters
            raise ValueError(f"Cannot determine format of pattern '{pattern}'")
    
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
            
            # Pad to multiple of 4 bits for hex alignment
            while len(binary_str) % 4 != 0:
                binary_str = '0' + binary_str
                
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
