"""Simulation ports."""

from typing import List

from hdltools.abshdl import HDLObject


class HDLBitVector(HDLObject):
    """Port slice."""

    def __init__(self, size, *bits):
        """Initialize."""
        if len(bits) != size:
            raise ValueError(
                f"incorrect amount of bits, expected {size}, got {len(bits)}"
            )

        self._values = bits

    @property
    def bits(self):
        """Get value."""
        return self._values

    def __len__(self):
        """Get length."""
        return len(self._values)

    def __getitem__(self, key):
        """Get item."""
        if isinstance(key, int):
            if key < 0 or key > len(self) - 1:
                raise IndexError
            return self._values[key]
        if isinstance(key, slice):
            raise NotImplementedError

        raise KeyError

    def __int__(self):
        """Get value as integer."""
        ret = 0
        for idx, value in enumerate(self._values):
            if value:
                ret += 1 << idx

        return ret

    def __bool__(self):
        """Get boolean value."""
        value = int(self)
        return value != 0

    def __add__(self, other):
        """Add two values."""
        if isinstance(other, int):
            raise NotImplementedError
        if isinstance(other, HDLBitVector):
            raise NotImplementedError
        raise TypeError

    def __or__(self, other):
        """Perform bitwise or operation."""
        if isinstance(other, int):
            val = int(self) | other
        elif isinstance(other, HDLBitVector):
            val = int(self) | int(other)
        else:
            raise TypeError
        return HDLBitVector(
            len(self), *self.bits_from_int(val, len(self), truncate=True)
        )

    def __and__(self, other):
        """Perform bitwise and operation."""
        if isinstance(other, int):
            val = int(self) & other
        elif isinstance(other, HDLBitVector):
            val = int(self) & int(other)
        else:
            raise TypeError
        return HDLBitVector(
            len(self), *self.bits_from_int(val, len(self), truncate=True)
        )

    def __xor__(self, other):
        """Perform bitwise xor operation."""
        if isinstance(other, int):
            val = int(self) ^ other
        elif isinstance(other, HDLBitVector):
            val = int(self) ^ int(other)
        else:
            raise TypeError
        return HDLBitVector(
            len(self), *self.bits_from_int(val, len(self), truncate=True)
        )

    @staticmethod
    def bits_from_int(value: int, size: int, truncate=False) -> List[bool]:
        """Get list of bits from integer value."""
        if not isinstance(value, int):
            raise TypeError("value must be integer")
        max_value = 2**size - 1
        if value > max_value and truncate is False:
            raise ValueError("value exceeds size")
        bits = []
        for idx in range(0, size):
            bits.append(True if value & (1 << idx) else False)

        return bits

    @staticmethod
    def value_fits(value: int, size: int) -> bool:
        """Determine if int value fits in bit vector."""
        max_value = 2**size - 1
        if value <= max_value:
            return True
        return False


class HDLSimulationPort(HDLObject):
    """Port representation."""

    def __init__(self, name, size=1, initial=0, change_cb=None):
        """Initialize."""
        self.name = name
        self.size = size
        self.initial = initial
        self._value = initial
        self._edge = None
        self._changed = False
        self._change_cb = change_cb

    @staticmethod
    def list_to_value(*values):
        """Get value from list of fragments."""
        ret = 0
        idx = 0
        reverse_list = values[::-1]
        for value in reverse_list:
            if isinstance(value, bool):
                if value:
                    ret += 1 << idx
                idx += 1
            else:
                raise TypeError("elements can only be integers")
        return ret

    @staticmethod
    def normalize_list_to_vector(_list):
        """Normalize heterogeneous list to vector of bits."""
        bits = []
        for item in _list:
            if isinstance(item, HDLBitVector):
                bits.extend(item.bits)
            elif isinstance(item, bool):
                bits.append(item)
            elif isinstance(item, int):
                if item not in (0, 1):
                    raise ValueError("integers can only be 0, 1")
                bits.append(bool(item))
            else:
                raise TypeError("list items must be bool or HDLBitVector")
        return bits

    def _value_change(self, value):
        """Record value change."""
        # for size of 1 bit only, detect edges
        if isinstance(value, list):
            value = self.normalize_list_to_vector(value)
            if len(value) != self.size:
                raise RuntimeError(
                    f"wrong number of elements, expected {self.size}, "
                    f"got {len(value)}"
                )
            value = self.list_to_value(*value)
        if self.size == 1:
            if bool(self._value ^ value) is True:
                if bool(self._value) is True:
                    self._edge = "fall"
                else:
                    self._edge = "rise"
            else:
                self._edge = None
        else:
            self._changed = bool(self._value != value)

        if self._value != value:
            if self._change_cb is not None:
                self._change_cb(self.name, self._value)

            self._value = value
            return True
        return False

    def rising_edge(self):
        """Is rising edge."""
        if self.size != 1:
            raise IOError("only applicable to ports of size 1")
        return bool(self._edge == "rise")

    def falling_edge(self):
        """Is falling edge."""
        if self.size != 1:
            raise IOError("only applicable to ports of size 1")
        return bool(self._edge == "fall")

    def value_changed(self):
        """Get value changed or not."""
        return bool(self._edge is not None or self._changed is True)

    def __getitem__(self, key):
        """Get piece of value."""
        if isinstance(key, int):
            if key > self.size - 1 or key < 0:
                raise IndexError
            return (self._value & (1 << key)) >> key
        if isinstance(key, slice):
            slice_size = abs(key.start - key.stop) + 1
            if slice_size == 1:
                return (self._value & (1 << key.start)) >> key.start
            bits = []
            if key.start > key.stop:
                start = key.stop
                stop = key.start
                invert = True
            else:
                start = key.start
                stop = key.stop
                invert = False
            for idx in range(start, stop + 1):
                if self._value & (1 << idx):
                    bits.append(True)
                else:
                    bits.append(False)
            if invert:
                bits = bits[::-1]
            return HDLBitVector(slice_size, *bits)

    def __setitem__(self, key, value):
        """Set piece of value."""
        if isinstance(key, int):
            if key > self.size or key < 0:
                raise IndexError
            if value:
                self._value |= 1 << key
            else:
                self._value &= ~(1 << key)
        elif isinstance(key, slice):
            slice_size = abs(key.start - key.stop) + 1
            max_value = 2**slice_size - 1
            if int(value) > max_value:
                raise ValueError("value exceeds slice size")
            if isinstance(value, HDLBitVector):
                if len(value) > slice_size:
                    raise ValueError("value size exceeds slice size")
                raise NotImplementedError
            if isinstance(value, int):
                bits = HDLBitVector.bits_from_int(value, slice_size)
                for idx in range(key.start, key.stop):
                    if bits[idx - key.start]:
                        self._value |= 1 << idx
                    else:
                        self._value &= ~(1 << idx)
            else:
                raise TypeError
        else:
            raise KeyError

    def __bool__(self):
        """Get boolean value."""
        return bool(self._value)

    def __int__(self):
        """Get integer value."""
        return self._value

    @property
    def value(self):
        """Get current value."""
        return self._value

    @property
    def bits(self):
        """Get bits."""
        return HDLBitVector.bits_from_int(self._value, self.size)

    def __len__(self):
        """Get size."""
        return self.size
