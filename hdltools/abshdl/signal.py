"""HDL Signals."""

from . import HDLObject
import hdltools.abshdl as hdl
from .stmt import HDLStatement
from .const import HDLIntegerConstant

# TODO allow multiple dimensions


class HDLSignal(HDLStatement):
    """HDL Signal."""

    _types = ['comb', 'reg', 'const', 'var']

    def __init__(self, sig_type, sig_name, size=1, default_val=None, **kwargs):
        """Initialize."""
        super(HDLSignal, self).__init__(stmt_type='par')
        if sig_type not in self._types:
            raise ValueError('invalid signal type: "{}"'.format(sig_type))

        self.sig_type = sig_type
        self.name = sig_name
        self.default_val = default_val

        if isinstance(size, int):
            # default is [size-1:0] / (size-1 downto 0)
            if (size < 0):
                raise ValueError('only positive size allowed')
            self.vector = hdl.vector.HDLVectorDescriptor(size-1, 0)
        elif isinstance(size, (tuple, list)):
            if len(size) != 2:
                raise ValueError('invalid vector '
                                 'dimensions: "{}"'.format(size))
            self.vector = hdl.vector.HDLVectorDescriptor(*size)
        elif isinstance(size, hdl.vector.HDLVectorDescriptor):
            self.vector = size
        elif isinstance(size, hdl.expr.HDLExpression):
            self.vector = hdl.vector.HDLVectorDescriptor(size-1)
        elif size == 'auto':
            if default_val is not None:
                eval_def_val = default_val.evaluate(**kwargs)
            else:
                raise ValueError('cannot determine size automatically')
            min_size = HDLIntegerConstant.minimum_value_size(eval_def_val)
            self.vector = hdl.vector.HDLVectorDescriptor(min_size)
        elif size is None:
            # allow this only for constants for now.
            if sig_type != 'const':
                raise ValueError('signal must have size')
            self.vector = None
        else:
            raise TypeError('size can only be of types: int, list or'
                            ' HDLVectorDescriptor')

    def __getitem__(self, key):
        """Slice of signal."""
        return HDLSignalSlice(self, key)

    def __repr__(self, eval_scope=None, decl=True):
        """Get readable representation."""
        if decl is True:
            if self.vector is None:
                vec = ''
            else:
                vec = self.vector.dumps(eval_scope)

            ret_str = '{} {}{} '.format(self.sig_type.upper(),
                                        self.name,
                                        vec)
        else:
            ret_str = self.name

        return ret_str

    def dumps(self, eval_scope=None, decl=True):
        """Alias for __repr__."""
        return self.__repr__(eval_scope=eval_scope,
                             decl=decl)

    def __len__(self):
        """Get length."""
        return len(self.vector)

    def is_legal(self):
        """Check legality."""
        return True


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
            self.vector = hdl.vector.HDLVectorDescriptor(slic, slic)
        elif isinstance(slic, (tuple, list)):
            if len(slic) != 2:
                raise ValueError('invalid vector '
                                 'dimensions: "{}"'.format(slic))
            self.vector = hdl.vector.HDLVectorDescriptor(*slic)
        elif isinstance(slic, hdl.vector.HDLVectorDescriptor):
            self.vector = slic
        elif isinstance(slic, slice):
            if slic.start is None:
                start = self.signal.vector.left_size
            else:
                start = slic.start
            self.vector = hdl.vector.HDLVectorDescriptor(start, slic.stop)
        else:
            raise TypeError('size can only be of types: int, list, slice, or'
                            ' HDLVectorDescriptor')

    def __repr__(self, eval_scope=None):
        """Get representation."""
        return '{}{}'.format(self.signal.name,
                             self.vector.dumps(eval_scope))

    def dumps(self, eval_scope=None):
        """Alias for __repr__."""
        return self.__repr__(eval_scope)

    def __len__(self):
        """Get length."""
        return len(self.vector)
