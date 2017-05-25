"""Sensitivity lists."""

from . import HDLObject
from .signal import HDLSignal, HDLSignalSlice


class HDLSensitivityDescriptor(HDLObject):
    """Signal sensitivity descriptor."""

    _sens_types = ['rise', 'fall', 'both', 'any']

    def __init__(self, sens_type, sig):
        """Initialize."""
        if sens_type not in self._sens_types:
            raise ValueError('illegal sensitivity'
                             ' type: "{}"'.format(sens_type))

        if not isinstance(sig, (HDLSignal, HDLSignalSlice)):
            raise TypeError('sig must be HDLSignal or HDLSignalSlice')

        self.sens_type = sens_type
        self.signal = sig

    def dumps(self):
        """Get representation."""
        if self.sens_type == 'rise':
            ret_str = 'rise({})'.format(self.signal.dumps(decl=False))
        elif self.sens_type == 'fall':
            ret_str = 'fall({})'.format(self.signal.dumps(decl=False))
        elif self.sens_type == 'both':
            ret_str = 'both({})'.format(self.signal.dumps(decl=False))
        elif self.sens_type == 'any':
            ret_str = self.signal.dumps(decl=False)

        return ret_str


class HDLSensitivityList(HDLObject):
    """Sensitivity list."""

    def __init__(self):
        """Initialize."""
        self.items = []

    def add(self, *descrs):
        """Add descriptors."""
        for descr in descrs:
            if not isinstance(descr, HDLSensitivityDescriptor):
                raise TypeError('only HDLSensitivityDescriptor allowed')

            # no duplicate checking!!!
            self.items.append(descr)

    def __len__(self):
        """Get item count."""
        return len(self.items)

    def __getitem__(self, _slice):
        """Get items."""
        return self.items[_slice]

    def dumps(self):
        """Get representation."""
        return '[{}]'.format(','.join([x.dumps() for x in self.items]))