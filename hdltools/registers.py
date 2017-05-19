"""HDL HDLRegister descriptors and actions."""


class HDLRegisterField(object):
    """Bitfield inside a register."""

    def __init__(self, name, reg_slice, permissions, properties=None):
        """Initialize."""
        self.name = name

        _slice = self._validate_slice(reg_slice)

        self.reg_slice = _slice
        self.permissions = permissions
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
            return range(self.reg_slice[1], self.reg_slice[0]+1)
        else:
            return self.reg_slice

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

    def add_properies(self, **properties):
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

    def get_write_mask(self):
        """Get register write access mask."""
        wr_mask = 0
        for field in self.fields:
            if field.permissions == 'R':
                continue

            for bit in field.get_range():
                wr_mask |= (1 << bit)

        return wr_mask
