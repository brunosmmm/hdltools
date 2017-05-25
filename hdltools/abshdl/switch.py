"""Switch / Case statements."""

from . import HDLObject
from .expr import HDLExpression
from .const import HDLIntegerConstant
from .scope import HDLScope
from .stmt import HDLStatement
from .signal import HDLSignal, HDLSignalSlice


class HDLSwitch(HDLStatement):
    """Switch Statement."""

    def __init__(self, what):
        """Initialize."""
        self.cases = {}
        if not isinstance(what, (HDLExpression, HDLSignal, HDLSignalSlice)):
            raise TypeError('only HDLExpression, HDLSignal,'
                            ' HDLSignalSlice allowed')

        # always use HDLExpression
        self.switch = HDLExpression(what)

    def add_case(self, case):
        """Add case."""
        if not isinstance(case, HDLCase):
            raise TypeError('only HDLCase allowed')

        # ideally want to detect duplicate but this could be difficult
        # with HDLExpression
        expr_repr = case.value.dumps()
        if expr_repr in self.cases:
            raise KeyError('trying to add duplicate case')

        self.cases[expr_repr] = case

    def dumps(self):
        """Intermediate representation."""
        ret_str = 'SWITCH {} BEGIN\n'.format(self.switch.dumps())
        for expr, case in self.cases:
            ret_str += case.dumps()

        ret_str += 'END\n'
        return ret_str


class HDLCase(HDLObject):
    """Switch case."""

    def __init__(self, value):
        """Initialize."""
        if isinstance(value, (HDLIntegerConstant, int)):
            self.case_value = HDLExpression(value)
        elif isinstance(value, HDLExpression):
            self.case_value = value
        else:
            raise TypeError('type "{}" '
                            'not supported'.format(value.__class__.__name__))

        self.scope = HDLScope()

    def add_to_scope(self, element):
        """Add statement to scope."""
        self.scope.add(element)

    def dumps(self):
        """Intermediate representation."""
        ret_str = '{}: BEGIN\n'.format(self.case_value.dumps())
        ret_str += '{}\n'.format(self.scope.dumps())
        ret_str += 'END\n'

        return ret_str
