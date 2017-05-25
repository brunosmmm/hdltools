"""Assignment."""

from .const import HDLIntegerConstant
from .expr import HDLExpression
from .signal import HDLSignal, HDLSignalSlice
from .concat import HDLConcatenation
from .stmt import HDLStatement


class HDLAssignment(HDLStatement):
    """Signal assignment."""

    def __init__(self, signal, value, assign_type='block'):
        """Initialize."""
        if not isinstance(signal, (HDLSignal, HDLSignalSlice)):
            raise TypeError('only HDLSignal, HDLSignalSlice can be assigned')

        self.assign_type = assign_type
        self.signal = signal
        if signal.sig_type in ('comb', 'const'):
            stmt_type = 'par'
        elif signal.sig_type in ('reg', 'var'):
            stmt_type = 'seq'
        else:
            raise ValueError('unknown signal '
                             'type: "{}"'.format(signal.sig_type))

        if isinstance(value, (HDLIntegerConstant,
                              HDLSignal, HDLExpression,
                              HDLSignalSlice, HDLConcatenation)):
            self.value = value
        elif isinstance(value, int):
            self.value = HDLIntegerConstant(value)
        else:
            raise TypeError('only integer, HDLIntegerConstant, '
                            'HDLSignal, HDLExpression, HDLConcatenation '
                            'allowed')

        super(HDLAssignment, self).__init__(stmt_type=stmt_type)

    def get_assignment_type(self):
        """Get assignment type."""
        if self.signal.sig_type in ('comb', 'const'):
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
        ret_str += self.value.dumps()

        return ret_str

    def is_legal(self):
        """Determine legality."""
        # always return True for now.
        return True
