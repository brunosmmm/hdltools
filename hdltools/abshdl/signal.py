"""HDL Signals."""

from . import HDLObject
from .vector import HDLVectorDescriptor

# TODO allow multiple dimensions


class HDLSignal(HDLObject):
    """HDL Signal."""

    _types = ['comb', 'reg']

    def __init__(self, sig_type, sig_name, size=1):
        """Initialize."""
        if sig_type not in self._types:
            raise ValueError('invalid signal type: "{}"'.format(sig_type))

        self.sig_type = sig_type
        self.name = sig_name

        if isinstance(size, int):
            # default is [size-1:0] / (size-1 downto 0)
            if (size < 0):
                raise ValueError('only positive size allowed')
            self.vector = HDLVectorDescriptor(size-1, 0)
        elif isinstance(size, (tuple, list)):
            if len(size) != 2:
                raise ValueError('invalid vector '
                                 'dimensions: "{}"'.format(size))
            self.vector = HDLVectorDescriptor(*size)
        elif isinstance(size, HDLVectorDescriptor):
            self.vector = size
        else:
            raise TypeError('size can only be of types: int, list or'
                            ' HDLVectorDescriptor')

    def __repr__(self, eval_scope=None):
        """Get readable representation."""
        return '{} {}{}'.format(self.sig_type.upper(),
                                self.name,
                                self.vector.dumps(eval_scope))

    def dumps(self, eval_scope=None):
        """Alias for __repr__."""
        return self.__repr__(eval_scope)


class HDLSignalSlice(HDLObject):
    """Slice of a vector signal."""

    def __init__(self, signal, slic):
        """Initialize."""
        if not isinstance(signal, HDLSignal):
            raise TypeError('only HDLSignal allowed')

        self.signal = signal

        if isinstance(slic, int):
            # default is [size-1:0] / (size-1 downto 0)
            if (slic < 0):
                raise ValueError('only positive integers allowed')
            self.vector = HDLVectorDescriptor(slic, slic)
        elif isinstance(slic, (tuple, list)):
            if len(slic) != 2:
                raise ValueError('invalid vector '
                                 'dimensions: "{}"'.format(slic))
            self.vector = HDLVectorDescriptor(*slic)
        elif isinstance(slic, HDLVectorDescriptor):
            self.vector = slic
        else:
            raise TypeError('size can only be of types: int, list or'
                            ' HDLVectorDescriptor')
