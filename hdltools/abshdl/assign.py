"""Assignment."""

from . import HDLObject
from .const import HDLIntegerConstant
from .expr import HDLExpression
from .signal import HDLSignal, HDLSignalSlice


class HDLAssignment(HDLObject):
    """Signal assignment."""

    def __init__(self, signal, value, assign_type='block'):
        """Initialize."""
        if not isinstance(signal, (HDLSignal, HDLSignalSlice)):
            raise TypeError('only HDLSignal, HDLSignalSlice can be assigned')

        self.assign_type = assign_type
        self.signal = signal

        if isinstance(value, (HDLIntegerConstant,
                              HDLSignal, HDLExpression,
                              HDLSignalSlice)):
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
