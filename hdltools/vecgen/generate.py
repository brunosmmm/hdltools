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
    _SYNTAX_ERRORS = {
        "t001": _SYNTAX_ERR_TIME_PAST,
        "v002": _SYNTAX_ERR_INVALID_NAME,
    }

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
        # Handle different value types
        if hasattr(node.val, '__class__') and hasattr(node.val, '_tx_class_name'):
            # This is a parsed object, get its value using the specific visitor
            class_name = node.val._tx_class_name
            if class_name == 'HexValue':
                val = self.visit_HexValue(node.val)
            elif class_name == 'BinValue':
                val = self.visit_BinValue(node.val)
            elif class_name == 'BooleanExpr':
                val = self.visit_BooleanExpr(node.val)
            else:
                # ID or other string value
                val = node.val
        else:
            val = node.val
        
        if isinstance(val, str):
            # symbol lookup
            if val not in self._definitions:
                raise self.get_error_from_code(node, "v002", name=val)

            val = self._definitions[val]

        self._current_time += 1
        return {"event": "initial", "value": val}

    def visit_SequenceElement(self, node):
        """Visit sequence element."""
        # Handle different mask types
        if hasattr(node.mask, '__class__') and hasattr(node.mask, '_tx_class_name'):
            # This is a parsed object, get its value using the specific visitor
            class_name = node.mask._tx_class_name
            if class_name == 'HexValue':
                mask = self.visit_HexValue(node.mask)
            elif class_name == 'BinValue':
                mask = self.visit_BinValue(node.mask)
            elif class_name == 'BooleanExpr':
                mask = self.visit_BooleanExpr(node.mask)
            else:
                # ID or other string value
                mask = node.mask
        else:
            mask = node.mask
        
        if isinstance(mask, str):
            # symbol lookup
            if mask not in self._definitions:
                raise self.get_error_from_code(node, "v002", name=mask)

            mask = self._definitions[mask]

        if node.time is None:
            self._current_time += 1
            # insert relative time
            time = {"mode": "rel", "delta": 1}
        else:
            # Handle time object
            if hasattr(node.time, '_tx_class_name'):
                class_name = node.time._tx_class_name
                if class_name == 'RelTimeValue':
                    time = self.visit_RelTimeValue(node.time)
                elif class_name == 'AbsTimeValue':
                    time = self.visit_AbsTimeValue(node.time)
                else:
                    time = node.time
            else:
                time = node.time
                
            if time["mode"] == "rel":
                self._current_time += time["delta"]
            else:
                abs_time = time["time"]
                if abs_time < self._current_time:
                    # time is in the past, cannot be
                    raise self.get_error_from_code(
                        node, "t001", cur=self._current_time, req=abs_time
                    )

                self._current_time = abs_time

        return {"event": node.event, "mask": mask, "time": time}

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
