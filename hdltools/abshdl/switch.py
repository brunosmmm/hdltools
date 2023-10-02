"""Switch / Case statements."""

from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.const import HDLIntegerConstant
from hdltools.abshdl.scope import HDLScope
from hdltools.abshdl.stmt import HDLStatement
from hdltools.abshdl.signal import HDLSignal, HDLSignalSlice
from hdltools.abshdl.macro import HDLMacroValue


class HDLSwitch(HDLStatement):
    """Switch Statement."""

    def __init__(self, what, **kwargs):
        """Initialize."""
        super().__init__(stmt_type="seq", has_scope=False, **kwargs)
        self.cases = {}
        if not isinstance(what, (HDLExpression, HDLSignal, HDLSignalSlice)):
            raise TypeError(
                "only HDLExpression, HDLSignal," " HDLSignalSlice allowed"
            )

        # always use HDLExpression
        self.switch = HDLExpression(what)

    def add_case(self, case):
        """Add case."""
        if not isinstance(case, HDLCase):
            raise TypeError("only HDLCase allowed")

        # ideally want to detect duplicate but this could be difficult
        # with HDLExpression
        expr_repr = case.case_value.dumps()
        if expr_repr in self.cases:
            raise KeyError("trying to add duplicate case")

        self.cases[expr_repr] = case
        case.set_parent(self)

    def get_case(self, expr):
        """Get case object."""
        if expr in self.cases:
            return self.cases[expr]

        raise KeyError('case not found: "{}"'.format(expr))

    def dumps(self):
        """Intermediate representation."""
        ret_str = "SWITCH {} BEGIN\n".format(self.switch.dumps())
        for expr, case in self.cases.items():
            ret_str += case.dumps()

        ret_str += "END\n"
        return ret_str

    def is_legal(self):
        """Determine legality."""
        if len(self.cases) == 0:
            return False

        return True

    def get_scope(self):
        """Get case scopes."""
        return [case.scope for name, case in self.cases.items()]


class HDLCase(HDLStatement):
    """Switch case."""

    def __init__(self, value, stmts=None, **kwargs):
        """Initialize."""
        super().__init__(has_scope=True, stmt_type="seq", **kwargs)
        if isinstance(value, (HDLIntegerConstant, int, str)):
            self.case_value = HDLExpression(value)
        elif isinstance(value, HDLExpression):
            self.case_value = value
        elif isinstance(value, HDLMacroValue):
            self.case_value = value
        else:
            raise TypeError(
                'type "{}" ' "not supported".format(value.__class__.__name__)
            )

        self.scope = HDLScope(scope_type="seq")
        if stmts is not None:
            for stmt in stmts:
                self.add_to_scope(stmt)

    def add_to_scope(self, *elements):
        """Add statement to scope."""
        self.scope.add(elements)

    def dumps(self):
        """Intermediate representation."""
        ret_str = "{}: BEGIN\n".format(self.case_value.dumps())
        ret_str += "{}\n".format(self.scope.dumps())
        ret_str += "END\n"

        return ret_str

    def is_legal(self):
        """Determine legality."""
        return True

    def get_scope(self):
        """Get scope."""
        return self.scope
