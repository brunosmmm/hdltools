"""Generate pass."""

from scoff.ast.visits.syntax import (
    SyntaxChecker,
    SyntaxCheckerError,
    SyntaxErrorDescriptor,
)


class VecgenPass(SyntaxChecker):
    """Visit AST and generate intermediate code."""

    _CONFIG_DIRECTIVES = ("register_size",)
    _SYNTAX_ERR_INVALID_VAL = SyntaxCheckerError("invalid value", "v001")
    _SYNTAX_ERR_INVALID_NAME = SyntaxCheckerError(
        "unknown name: '{name}'", "v002"
    )
    _SYNTAX_ERR_TIME_PAST = SyntaxErrorDescriptor(
        "t001",
        "absolute time is in the past",
        "absolute time is in the past, current time is {cur}, requested is {req}",
    )
    _SYNTAX_ERRORS = {"t001": _SYNTAX_ERR_TIME_PAST}

    def __init__(self, *args, **kwargs):
        """Initialize."""
        super().__init__(*args, **kwargs)
        self._sequence = []
        self._definitions = {}
        self._directives = {}
        self._current_time = 0

    def visit_ConfigurationDirective(self, node):
        """Visit configuration directive."""
        if node.directive not in self._CONFIG_DIRECTIVES:
            # unknown, ignore for now
            return

        if node.directive in self._directives:
            # re-define, warning
            pass

        # store
        self._directives[node.directive] = node.value

    def visit_ValueDefinition(self, node):
        """Visit value definition."""
        if node.name in self._definitions:
            # re-define, warning
            pass

        self._definitions[node.name] = node.value

    def visit_InitialElement(self, node):
        """Visit initial element."""
        if isinstance(node.val, str):
            # symbol lookup
            if node.val not in self._definitions:
                raise self.get_error_from_code(node, "v002", name=node.val)

            node.val = self._definitions[node.val]

        self._current_time += 1
        return {"event": "initial", "value": node.val}

    def visit_SequenceElement(self, node):
        """Visit sequence element."""
        if isinstance(node.mask, str):
            # symbol lookup
            if node.mask not in self._definitions:
                raise self.get_error_from_code(node, "v002", name=node.mask)

            node.mask = self._definitions[node.mask]

        if node.time is None:
            self._current_time += 1
            # insert relative time
            time = {"mode": "rel", "delta": 1}
        else:
            if node.time["mode"] == "rel":
                self._current_time += node.time["delta"]
            else:
                abs_time = node.time["time"]
                if abs_time < self._current_time:
                    # time is in the past, cannot be
                    raise self.get_error_from_code(
                        node, "t001", cur=self._current_time, req=abs_time
                    )

                self._current_time = abs_time
            time = node.time

        return {"event": node.event, "mask": node.mask, "time": time}

    def visit_HexValue(self, node):
        """Visit hexadecimal value."""
        try:
            value = int(node.val, 16)
        except ValueError:
            raise self._SYNTAX_ERR_INVALID_VAL

        return value

    def visit_BinValue(self, node):
        """Visit binary value."""
        try:
            value = int(node.val, 2)
        except ValueError:
            raise self._SYNTAX_ERR_INVALID_VAL

        return value

    def visit_AbsTimeValue(self, node):
        """Visit absolute time value."""
        if node.time < 0:
            raise self._SYNTAX_ERR_INVALID_VAL

        return {"mode": "abs", "time": node.time}

    def visit_RelTimeValue(self, node):
        """Visit relative time value."""
        if node.time < 0:
            raise self._SYNTAX_ERR_INVALID_VAL

        return {"mode": "rel", "delta": node.time}

    def visit_VectorDescription(self, node):
        """Visit AST root."""
        ir = self._directives
        ir["sequence"] = [node.initial] + node.sequence

        # doesnt return, not sure why
        self._sequence = ir
        return ir

    def visit_BitwiseBinOperation(self, node):
        """Visit binary bitwise operation."""
        if node.op == "<<":
            return node.lhs << node.rhs
        elif node.op == ">>":
            return node.lhs >> node.rhs
        elif node.op == "|":
            return node.lhs | node.rhs
        elif node.op == "&":
            return node.lhs & node.rhs
        elif node.op == "^":
            return node.lhs ^ node.rhs
        else:
            # cannot happen!
            return None

    def visit_BitwiseNegate(self, node):
        """Visit negation."""
        return ~node.val

    def visit_BooleanExpr(self, node):
        """Visit boolean expression."""
        return node.op

    def visit_Comment(self, node):
        """Visit comment."""

    def visit(self, node):
        """Perform visit."""
        ret = super().visit(node)
        return self._sequence
