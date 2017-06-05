"""Assignment."""

from .const import HDLIntegerConstant
from .expr import HDLExpression
from .signal import HDLSignal, HDLSignalSlice
from .concat import HDLConcatenation
from .stmt import HDLStatement
from .module import HDLModulePort
from .ifelse import HDLIfExp


class HDLAssignment(HDLStatement):
    """Signal assignment."""

    def __init__(self, signal, value, assign_type='block', **kwargs):
        """Initialize."""
        if isinstance(signal, HDLModulePort):
            if signal.direction in ('out', 'inout'):
                signal = signal.signal
            else:
                raise ValueError('cannot assign to input port')

        if not isinstance(signal, (HDLSignal, HDLSignalSlice)):
            raise TypeError('only HDLSignal, HDLSignalSlice can be assigned')

        self.assign_type = assign_type
        self.signal = signal

        if isinstance(signal, HDLSignal):
            sig_type = signal.sig_type
        elif isinstance(signal, HDLSignalSlice):
            sig_type = signal.signal.sig_type

        if sig_type in ('comb', 'const'):
            stmt_type = 'par'
        elif sig_type in ('reg', 'var'):
            stmt_type = 'seq'

        if isinstance(value, (HDLIntegerConstant,
                              HDLSignal, HDLExpression,
                              HDLSignalSlice, HDLConcatenation,
                              HDLIfExp)):
            self.value = value
        elif isinstance(value, int):
            self.value = HDLIntegerConstant(value, **kwargs)
        else:
            raise TypeError('only integer, HDLIntegerConstant, '
                            'HDLSignal, HDLExpression, HDLConcatenation, '
                            'HDLIfExp '
                            'allowed, got: {}'.format(
                                value.__class__.__name__))

        super(HDLAssignment, self).__init__(stmt_type=stmt_type)

    def get_assignment_type(self):
        """Get assignment type."""
        if isinstance(self.signal, HDLSignal):
            sig_type = self.signal.sig_type
        elif isinstance(self.signal, HDLSignalSlice):
            sig_type = self.signal.signal.sig_type

        if sig_type in ('comb', 'const'):
            return 'parallel'
        else:
            return 'series'

    def dumps(self):
        """Get representation."""
        ret_str = self.signal.dumps(decl=False)
        if self.signal.sig_type in ('comb', 'const'):
            ret_str += ' = '
        else:
            ret_str += ' <= '
        ret_str += self.value.dumps()+';'

        return ret_str

    def is_legal(self):
        """Determine legality."""
        # always return True for now.
        return True
