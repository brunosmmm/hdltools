"""HDL HDLRegister descriptors and actions."""

from .concat import HDLConcatenation
from .expr import HDLExpression


class HDLRegisterField(object):
    """Bitfield inside a register."""

    def __init__(self, name, reg_slice,
                 permissions, default_value=0, properties=None):
        """Initialize."""
        self.name = name

        _slice = self._validate_slice(reg_slice)

        self.reg_slice = _slice
        self.permissions = permissions
        self.default_value = default_value
        if properties is not None:
            self.properties = dict(properties)
        else:
            self.properties = {}

    def _validate_slice(self, reg_slice):
        if isinstance(reg_slice, (tuple, list)):
            if len(reg_slice) > 2:
                raise ValueError('invalid range')
            return reg_slice
        elif isinstance(reg_slice, int):
            return [reg_slice]
        else:
            raise TypeError('invalid type '
                            'for slice: "{}"'.format(type(reg_slice)))

    def add_properties(self, **kwargs):
        """Add a property."""
        self.properties.update(kwargs)

    def get_range(self):
        """Get which bits are claimed by this field."""
        if len(self.reg_slice) > 1:
            return list(range(self.reg_slice[1], self.reg_slice[0]+1))
        else:
            return self.reg_slice

    def get_slice(self):
        """Get a slice object."""
        if len(self.reg_slice) > 1:
            return slice(self.reg_slice[0], self.reg_slice[1])
        else:
            return self.reg_slice[0]

    def dumps_slice(self):
        """Print formatted slice."""
        if len(self.reg_slice) == 2:
            return '[{}..{}]'.format(*self.reg_slice)
        else:
            return '[{}]'.format(self.reg_slice[0])


class HDLRegister(object):
    """Register."""

    def __init__(self, name, size, addr):
        """Initialize."""
        self.name = name
        self.size = size
        self.addr = addr
        self.fields = []
        self.properties = {}

    def get_used_bits(self):
        """Get which bits are already claimed by fields."""
        bits = []
        for field in self.fields:
            bits.extend(field.get_range())

        return bits

    def add_properties(self, **properties):
        """Add a property."""
        self.properties.update(properties)

    def check_bit_clash(self, bit_list):
        """Check if bits in list clash with pre-existing fields."""
        clashes = []
        for bit in bit_list:
            if bit in self.get_used_bits():
                clashes.append(bit)

        if len(clashes) == 0:
            return None

        return clashes

    def add_fields(self, *args):
        """Add fields."""
        for arg in args:
            if not isinstance(arg, HDLRegisterField):
                raise TypeError('only HDLRegisterField type allowed')

            # check clashes
            clashes = self.check_bit_clash(arg.get_range())
            if clashes is not None:
                raise ValueError('Cannot insert field,'
                                 ' bits "{}" already reserved'.format(clashes))

            # else, insert
            self.fields.append(arg)

    def has_field(self, field_name):
        """Check if field is present."""
        for field in self.fields:
            if field.name == field_name:
                return True

        return False

    def get_field(self, field_name):
        """Get a field object."""
        for field in self.fields:
            if field.name == field_name:
                return field

        raise KeyError('invalid field: "{}"'.format(field_name))

    def get_write_mask(self):
        """Get register write access mask."""
        wr_mask = 0
        for field in self.fields:
            if field.permissions == 'R':
                continue

            for bit in field.get_range():
                wr_mask |= (1 << bit)

        return wr_mask

    def get_default_value(self):
        """Get register default value."""
        # detect field types

        has_expr = False
        for field in self.fields:
            if isinstance(field.default_value, HDLExpression):
                has_expr = True
                break

        if has_expr is False:
            val = 0
            for field in self.fields:
                field_offset = field.get_range()[0]

                val |= (field.default_value << field_offset)

            return val
        else:
            val = HDLConcatenation()
            for field in sorted(self.fields,
                                key=lambda x: x.reg_slice[0])[::-1]:
                val.append(field.default_value)

            return val
