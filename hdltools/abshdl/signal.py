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
        if isinstance(default_val, hdl.expr.HDLExpression):
            self.default_val = default_val
        elif default_val is None:
            self.default_val = default_val
        else:
            self.default_val = hdl.expr.HDLExpression(default_val)

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
            if sig_type not in ('const', 'var'):
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

    # TODO rewrite docstrings

    def __add__(self, other):
        """Add expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return hdl.expr.HDLExpression(self) + other

    def __radd__(self, other):
        """Add expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as left-hand side
        """
        return other + hdl.expr.HDLExpression(self)

    def __sub__(self, other):
        """Subtract expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return hdl.expr.HDLExpression(self) - other

    def __rsub__(self, other):
        """Subtract expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as left-hand side
        """
        return other - hdl.expr.HDLExpression(self)

    def __mul__(self, other):
        """Multiply expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return hdl.expr.HDLExpression(self) * other

    def __rmul__(self, other):
        """Multiply expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as left-hand side
        """
        return other * hdl.expr.HDLExpression(self)

    def __truediv__(self, other):
        """Divide expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return hdl.expr.HDLExpression(self) / other

    def __lshift__(self, val):
        """Shift operator."""
        return hdl.expr.HDLExpression(self) << val

    def __rshift__(self, val):
        """Shift operator."""
        return hdl.expr.HDLExpression(self) >> val

    def __or__(self, other):
        """Bitwise OR."""
        return hdl.expr.HDLExpression(self) | other

    def __ror__(self, other):
        """Reverse Bitwise OR."""
        return other | hdl.expr.HDLExpression(self)

    def __and__(self, other):
        """Bitwise AND."""
        return hdl.expr.HDLExpression(self) & other

    def __rand__(self, other):
        """Reverse Bitwise AND."""
        return other & hdl.expr.HDLExpression(self)

    def __xor__(self, other):
        """Bitwise XOR."""
        return hdl.expr.HDLExpression(self) ^ other

    def __rxor__(self, other):
        """Reverse Bitwise XOR."""
        return other ^ hdl.expr.HDLExpression(self)

    def __invert__(self):
        """Bitwise negation."""
        return ~hdl.expr.HDLExpression(self)

    def bool_neg(self):
        """Boolean negation."""
        return hdl.expr.HDLExpression(self).bool_neg()

    def bool_and(self, other):
        """Boolean AND."""
        return hdl.expr.HDLExpression(self).bool_and(other)

    def bool_or(self, other):
        """Boolean OR."""
        return hdl.expr.HDLExpression(self).bool_or(other)

    def __eq__(self, other):
        """Comparison."""
        return hdl.expr.HDLExpression(self) == other

    def __ne__(self, other):
        """Not equal."""
        return hdl.expr.HDLExpression(self) != other

    def __gt__(self, other):
        """Greater than."""
        return hdl.expr.HDLExpression(self) > other

    def __lt__(self, other):
        """Less than."""
        return hdl.expr.HDLExpression(self) < other

    def __ge__(self, other):
        """Greater or equal."""
        return hdl.expr.HDLExpression(self) >= other

    def __le__(self, other):
        """Less or equal."""
        return hdl.expr.HDLExpression(self) <= other

    def __pos__(self):
        """Get an expression for the signal."""
        return hdl.expr.HDLExpression(self)

    def assign(self, value, **kwargs):
        """Return an assignment."""
        if self.sig_type == 'var':
            assign_type = 'nonblock'
        else:
            assign_type = 'block'
        return hdl.assign.HDLAssignment(self, value, assign_type=assign_type,
                                        **kwargs)

    def get_sig_type(self):
        """Get signal type."""
        return self.sig_type


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
        elif isinstance(slic, HDLSignal):
            self.vector = hdl.vector.HDLVectorDescriptor(slic, slic)
        else:
            raise TypeError('size can only be of types: int, list, slice,'
                            ' HDLVectorDescriptor or HDLSignal')

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

    def assign(self, value, **kwargs):
        """Return an assignment."""
        return hdl.assign.HDLAssignment(self, value, **kwargs)

    def __add__(self, other):
        """Add expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return hdl.expr.HDLExpression(self) + other

    def __radd__(self, other):
        """Add expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as left-hand side
        """
        return other + hdl.expr.HDLExpression(self)

    def __sub__(self, other):
        """Subtract expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return hdl.expr.HDLExpression(self) - other

    def __rsub__(self, other):
        """Subtract expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as left-hand side
        """
        return other - hdl.expr.HDLExpression(self)

    def __mul__(self, other):
        """Multiply expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return hdl.expr.HDLExpression(self) * other

    def __rmul__(self, other):
        """Multiply expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as left-hand side
        """
        return other * hdl.expr.HDLExpression(self)

    def __truediv__(self, other):
        """Divide expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return hdl.expr.HDLExpression(self) / other

    def __lshift__(self, val):
        """Shift operator."""
        return hdl.expr.HDLExpression(self) << val

    def __rshift__(self, val):
        """Shift operator."""
        return hdl.expr.HDLExpression(self) >> val

    def __or__(self, other):
        """Bitwise OR."""
        return hdl.expr.HDLExpression(self) | other

    def __ror__(self, other):
        """Reverse Bitwise OR."""
        return other | hdl.expr.HDLExpression(self)

    def __and__(self, other):
        """Bitwise AND."""
        return hdl.expr.HDLExpression(self) & other

    def __rand__(self, other):
        """Reverse Bitwise AND."""
        return other & hdl.expr.HDLExpression(self)

    def __xor__(self, other):
        """Bitwise XOR."""
        return hdl.expr.HDLExpression(self) ^ other

    def __rxor__(self, other):
        """Reverse Bitwise XOR."""
        return other ^ hdl.expr.HDLExpression(self)

    def __invert__(self):
        """Bitwise negation."""
        return ~hdl.expr.HDLExpression(self)

    def bool_neg(self):
        """Boolean negation."""
        return hdl.expr.HDLExpression(self).bool_neg()

    def bool_and(self, other):
        """Boolean AND."""
        return hdl.expr.HDLExpression(self).bool_and(other)

    def bool_or(self, other):
        """Boolean OR."""
        return hdl.expr.HDLExpression(self).bool_or(other)

    def __eq__(self, other):
        """Comparison."""
        return hdl.expr.HDLExpression(self) == other

    def __ne__(self, other):
        """Not equal."""
        return hdl.expr.HDLExpression(self) != other

    def __gt__(self, other):
        """Greater than."""
        return hdl.expr.HDLExpression(self) > other

    def __lt__(self, other):
        """Less than."""
        return hdl.expr.HDLExpression(self) < other

    def __ge__(self, other):
        """Greater or equal."""
        return hdl.expr.HDLExpression(self) >= other

    def __le__(self, other):
        """Less or equal."""
        return hdl.expr.HDLExpression(self) <= other

    def __pos__(self):
        """Get an expression"""
        return hdl.expr.HDLExpression(self)

    def get_sig_type(self):
        """Get signal type."""
        return self.signal.sig_type
