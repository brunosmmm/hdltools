"""Assignment."""

from . import HDLObject, HDLIntegerConstant
from .expr import HDLExpression
from .signal import HDLSignal


class HDLAssignment(HDLObject):
    """Signal assignment."""

    def __init__(self, signal, value):
        """Initialize."""
        if not isinstance(signal, HDLSignal):
            raise TypeError('only HDLSignal can be assigned')

        self.signal = signal

        if isinstance(value, (HDLIntegerConstant, HDLSignal, HDLExpression)):
            self.value = value
        elif isinstance(value, int):
            self.value = HDLIntegerConstant(value)
        else:
            raise TypeError('only integer, HDLIntegerConstant,'
                            'HDLSignal, HDLExpression allowed')

    def get_assignment_type(self):
        """Get assignment type."""
        if self.signal.sig_type == 'comb':
            return 'parallel'
        else:
            return 'series'
