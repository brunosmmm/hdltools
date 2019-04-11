"""For Loops."""

from .stmt import HDLStatement
from .expr import HDLExpression
from .assign import HDLAssignment
from .scope import HDLScope


class HDLForLoop(HDLStatement):
    """For loop."""

    def __init__(self, init, stop_condition, afterthought, **kwargs):
        """Initialize."""
        super().__init__(has_scope=True, stmt_type="seq", **kwargs)
        self.scope = HDLScope(scope_type="seq")

        if not isinstance(init, HDLAssignment):
            raise TypeError(
                "initialization argument must be a " " HDLAssignment object"
            )

        self.init = init

        if not isinstance(stop_condition, HDLExpression):
            raise TypeError("stop condition must be a HDLExpression object")

        self.stop = stop_condition

        if not isinstance(afterthought, HDLAssignment):
            raise TypeError("afterthought must be a HDLAssignment object")

        self.after = afterthought

    def add_to_scope(self, *elements):
        """Add to scope."""
        self.scope.add(elements)

    def is_legal(self):
        """Check legality."""
        if len(self.scope) > 0:
            return True

        return False


class HDLForRange(HDLForLoop):
    """For loop using range."""

    pass
