"""IF-ELSE constructs."""

from .stmt import HDLStatement
from .scope import HDLScope
from .expr import HDLExpression
from .signal import HDLSignal, HDLSignalSlice


class HDLIfElse(HDLStatement):
    """If-Else statement."""

    def __init__(self, condition, if_scope=None, else_scope=None):
        """Initialize."""
        super(HDLIfElse, self).__init__(stmt_type='seq')
        self.if_scope = HDLScope(scope_type='seq')
        self.else_scope = HDLScope(scope_type='seq')
        if not isinstance(condition, (HDLExpression, HDLSignal,
                                      HDLSignalSlice)):
            raise TypeError('only HDLEXpression, HDLSignal,'
                            ' HDLSignalSlice allowed')

        # Always use HDLExpression
        self.condition = HDLExpression(condition)

        if if_scope is not None:
            self.add_to_if_scope(if_scope)
        if else_scope is not None:
            self.add_to_else_scope(else_scope)

    def add_to_if_scope(self, *stmt):
        """Add to IF scope."""
        self.if_scope.add(stmt)

    def add_to_else_scope(self, *stmt):
        """Add to ELSE scope."""
        self.else_scope.add(stmt)

    def dumps(self):
        """Get Intermediate representation."""
        ret_str = 'IF {} BEGIN\n'.format(self.condition.dumps())
        ret_str += self.if_scope.dumps()
        ret_str += 'END\n'

        if len(self.else_scope) > 0:
            ret_str += 'ELSE BEGIN\n'
            ret_str += self.else_scope.dumps()
            ret_str += 'END\n'

        return ret_str

    def is_legal(self):
        """Determine if legal."""
        if len(self.if_scope) == 0:
            return False

        return True
