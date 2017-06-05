"""IF-ELSE constructs."""

from .stmt import HDLStatement
from .scope import HDLScope
from .expr import HDLExpression
from .signal import HDLSignal, HDLSignalSlice


class HDLIfElse(HDLStatement):
    """If-Else statement."""

    def __init__(self, condition, if_scope=None, else_scope=None, **kwargs):
        """Initialize."""
        super(HDLIfElse, self).__init__(stmt_type='seq',
                                        has_scope=True,
                                        **kwargs)
        self.if_scope = HDLScope(scope_type='seq')
        self.else_scope = HDLScope(scope_type='seq')
        if not isinstance(condition, (HDLExpression, HDLSignal,
                                      HDLSignalSlice)):
            raise TypeError('only HDLExpression, HDLSignal,'
                            ' HDLSignalSlice allowed, got:'
                            ' {}'.format(condition.__class__.__name__))

        # Always use HDLExpression
        self.condition = HDLExpression(condition)

        if if_scope is not None:
            if isinstance(if_scope, (tuple, list)):
                self.add_to_if_scope(*if_scope)
            else:
                self.add_to_if_scope(if_scope)
        if else_scope is not None:
            if isinstance(else_scope, (tuple, list)):
                self.add_toelse_scope(*else_scope)
            else:
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
        ret_str += '\nEND'

        if len(self.else_scope) > 0:
            ret_str += '\nELSE BEGIN\n'
            ret_str += self.else_scope.dumps()
            ret_str += '\nEND'

        return ret_str

    def is_legal(self):
        """Determine if legal."""
        if len(self.if_scope) == 0:
            return False

        return True

    def get_scope(self):
        """Get Scope."""
        return (self.if_scope, self.else_scope)


class HDLIfExp(HDLStatement):
    """One line if-else expressions."""

    def __init__(self, condition, if_value, else_value, **kwargs):
        """Initialize."""
        super().__init__(stmt_type='par', **kwargs)
        self.condition = condition
        self.if_value = if_value
        self.else_value = else_value

        if not isinstance(condition, (HDLExpression, HDLSignal,
                                      HDLSignalSlice)):
            raise TypeError('only HDLExpression, HDLSignal,'
                            ' HDLSignalSlice allowed, got:'
                            ' {}'.format(condition.__class__.__name__))

        self.condition = HDLExpression(condition)

    def is_legal(self):
        """Determine if legal."""
        if self.if_value is None or self.else_value is None:
            return False

        return True

    def dumps(self):
        """Get representation."""
        ret_str = '{} ? {} else {}'.format(self.condition.dumps(),
                                           self.if_value,
                                           self.else_value)
        return ret_str
