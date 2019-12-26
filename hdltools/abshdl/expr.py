"""HDL Expressions."""

from . import HDLValue
from .const import HDLIntegerConstant
import hdltools.abshdl.signal as signal
import ast
import operator as op
import copy


class HDLExpression(HDLValue):
    """An expression involving parameters."""

    _ast_op_names = {
        ast.Sub: "-",
        ast.Add: "+",
        ast.Mult: "*",
        ast.Div: "/",
        ast.LShift: "<<",
        ast.RShift: ">>",
        ast.BitOr: "|",
        ast.BitAnd: "&",
        ast.BitXor: "^",
        ast.Or: "||",
        ast.And: "&&",
        ast.Invert: "~",
        ast.Not: "!",
        ast.Eq: "==",
        ast.NotEq: "!=",
        ast.Lt: "<",
        ast.Gt: ">",
        ast.GtE: ">=",
        ast.LtE: "=<",
        ast.Is: "==",
    }
    _operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Pow: op.pow,
        ast.USub: op.neg,
        ast.LShift: op.lshift,
        ast.RShift: op.rshift,
        ast.BitOr: op.or_,
        ast.BitAnd: op.and_,
        ast.BitXor: op.xor,
        ast.Or: lambda x, y: bool(x or y),
        ast.And: lambda x, y: bool(x and y),
        ast.Invert: op.invert,
        ast.Not: op.not_,
        ast.Eq: op.eq,
        ast.NotEq: op.ne,
        ast.Lt: op.lt,
        ast.Gt: op.gt,
        ast.LtE: op.le,
        ast.GtE: op.ge,
        ast.Is: op.eq,
    }

    def __init__(self, value, size=None, **kwargs):
        """Initialize.

        Args
        ----
        expr_tree: ast.Expression
            Expression tree
        """
        super().__init__()
        if isinstance(value, HDLExpression):
            self.tree = copy.copy(value.tree)
            self.size = value.size
            self.from_type = "expr"
        elif isinstance(value, str):
            self.tree = ast.parse(value, mode="eval")
            self.size = size
            self.from_type = "const"
        elif isinstance(value, ast.Expression):
            self.tree = value
            self.size = size
            self.from_type = "expr"
        elif isinstance(value, HDLIntegerConstant):
            self.tree = ast.Expression(body=ast.Num(n=value.value))
            self.size = len(value)
            self.from_type = "const"
        elif isinstance(value, int):
            self.tree = ast.Expression(body=ast.Num(n=value))
            if size is None:
                # automatically generate size
                self.size = HDLIntegerConstant.minimum_value_size(value)
            else:
                self.size = size
            self.from_type = "const"
        elif isinstance(value, signal.HDLSignal):
            self.tree = ast.Expression(body=ast.Name(id=value.name))
            try:
                self.size = len(value)
            except TypeError:
                if value.sig_type in ("const", "var"):
                    self.size = None
                else:
                    raise
            self.from_type = "signal"
        elif isinstance(value, signal.HDLSignalSlice):
            name = ast.Name(id=value.signal.name)
            # if len(value.vector) > 1:
            _slice = ast.Slice(
                upper=value.vector.left_size.tree,
                lower=value.vector.right_size.tree,
                step=None,
            )
            # else:
            #    _slice = ast.Index(value=value.vector.left_size.tree)
            self.tree = ast.Expression(
                body=ast.Subscript(value=name, slice=_slice)
            )
            try:
                self.size = len(value)
            except KeyError:
                # could not determine size
                self.size = None
            self.from_type = "signal"
        elif isinstance(value, ast.Compare):
            self.tree = value
            self.size = size
            self.from_type = "expr"
        else:
            raise TypeError(
                "invalid type provided: " "{}".format(value.__class__.__name__)
            )

        # store kwargs
        self.optional_args = kwargs

    def __len__(self):
        """Get width, if known."""
        if self.size is None:
            raise ValueError("cannot determine total length")
        else:
            return self.size

    def evaluate(self, **kwargs):
        """Evaluate current expression.

        Args
        ----
        kwargs: dict
           Dictionary which must contain all necessary symbols to evaluate
        """
        return self._evaluate(self.tree, **kwargs)

    def _evaluate(self, node, **kwargs):
        """Evaluate current expression.

        Args
        ----
        kwargs: dict
           Dictionary which must contain all necessary symbols to evaluate
        """
        if isinstance(node, ast.Expression):
            return self._evaluate(node.body, **kwargs)
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Name):
            if node.id in kwargs:
                return kwargs[node.id]
            else:
                raise KeyError(node.id)
        elif isinstance(node, (ast.BinOp, ast.BoolOp)):
            return self._operators[type(node.op)](
                self._evaluate(node.left, **kwargs),
                self._evaluate(node.right, **kwargs),
            )
        elif isinstance(node, ast.UnaryOp):
            return self._operators[type(node.op)](
                self._evaluate(node.operand, **kwargs)
            )
        elif isinstance(node, ast.Call):
            if node.func.id in kwargs:
                # evaluate arguments
                arg_eval = []
                for arg in node.args:
                    arg_eval.append(self._evaluate(arg, **kwargs))

                return kwargs[node.func.id].call(*arg_eval, **kwargs)
            else:
                raise KeyError(
                    'function "{}" not' " available".format(node.func.id)
                )
        elif isinstance(node, ast.Subscript):
            signal_name = self._evaluate(node.value)
            _slice = self._evaluate(node.slice)
            # return string only
            return signal_name + _slice
        elif isinstance(node, ast.Index):
            return "[{}]".format(self._evaluate(node.value))
        elif isinstance(node, ast.Slice):
            return "[{}:{}]".format(
                self._evaluate(node.upper), self._evaluate(node.lower)
            )

        else:
            raise TypeError(node)

    def _get_expr(self, node):
        # TODO: eliminate unnecessary parentheses
        if isinstance(node, ast.Expression):
            return self._get_expr(node.body)
        elif isinstance(node, ast.BoolOp):
            op_str = "{}".format(self._ast_op_names[node.op.__class__])
            values = [self._get_expr(val) for val in node.values]
            return "({})".format(op_str.join(values))
        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.op, (ast.UAdd, ast.USub)):
                raise TypeError("operator not supported")
            op_str = self._ast_op_names[node.op.__class__]
            return "{}{}".format(op_str, self._get_expr(node.operand))
        elif isinstance(node, ast.BinOp):
            left_expr = self._get_expr(node.left)
            right_expr = self._get_expr(node.right)

            return "({}{}{})".format(
                left_expr, self._ast_op_names[node.op.__class__], right_expr
            )
        elif isinstance(node, ast.Num):
            return str(node.n)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.NameConstant):
            return node.value
        elif isinstance(node, ast.Call):
            arg_list = []
            for arg in node.args:
                arg_list.append(self._get_expr(arg))
            return "{}({})".format(node.func.id, ",".join(arg_list))
        elif isinstance(node, ast.Compare):
            if len(node.ops) > 1:
                raise ValueError("multiple inline comparison not supported")
            left = self._get_expr(node.left)
            comp = self._get_expr(node.comparators[0])
            return "{} {} {}".format(
                left, self._ast_op_names[node.ops[0].__class__], comp
            )
        elif isinstance(node, ast.Subscript):
            signal_name = self._get_expr(node.value)
            _slice = self._get_expr(node.slice)
            # return string only
            return signal_name + _slice
        elif isinstance(node, ast.Index):
            # NOTICE: THIS IS LANGUAGE DEPENDENT!!!!!!
            return "[{}]".format(self._get_expr(node.value))
        elif isinstance(node, ast.Slice):
            upper = self._get_expr(node.upper)
            lower = self._get_expr(node.lower)
            if upper != lower:
                return "[{}:{}]".format(upper, lower)
            else:
                return "[{}]".format(upper)
        else:
            raise TypeError('invalid type: "{}"'.format(type(node)))

    def __repr__(self):
        """Get representation of expression."""
        return self._get_expr(self.tree)

    def dumps(self):
        """Alias for __repr__."""
        return self.__repr__()

    @classmethod
    def _get_reverse_operator_mapping(cls):
        reverse_dict = {}
        for key, value in cls._ast_op_names.items():
            reverse_dict[value] = key

        return reverse_dict

    @classmethod
    def combine_expressions(cls, lhs, op, rhs):
        """Combine two expressions into a new BinOp.

        Args
        ----
        lhs: HDLExpression
           left-hand side operand
        op: str
           operation descriptor string
        rhs: HDLExpression
           right-hand side operand
        """
        if not isinstance(lhs, HDLExpression) or not isinstance(
            rhs, HDLExpression
        ):
            raise TypeError("can only combine two HDLExpression objects")

        # check operator?
        op_mapping = cls._get_reverse_operator_mapping()
        if op not in op_mapping:
            raise ValueError('illegal operator: "{}"'.format(op))

        if op in ("||", "&&"):
            new_op = ast.BoolOp(
                op=op_mapping[op](),
                values=[copy.copy(lhs.tree), copy.copy(rhs.tree)],
            )
        elif op in (">", "<", "==", "!=", ">=", "=<"):
            new_op = ast.Compare(
                ops=[op_mapping[op]()],
                left=copy.copy(lhs.tree),
                comparators=[copy.copy(rhs.tree)],
            )
        else:
            new_op = ast.BinOp(
                left=copy.copy(lhs.tree),
                op=op_mapping[op](),
                right=copy.copy(rhs.tree),
            )
        return HDLExpression(ast.Expression(body=new_op))

    def _new_binop(self, op, other, this_lhs=True):
        if isinstance(other, HDLExpression):
            rhs = other
        elif isinstance(
            other,
            (HDLIntegerConstant, signal.HDLSignal, signal.HDLSignalSlice, int),
        ):
            rhs = HDLExpression(other)
        else:
            raise TypeError('illegal type: "{}"'.format(type(other)))
        # create new BinOp
        if this_lhs is True:
            return self.combine_expressions(self, op, rhs)
        else:
            return self.combine_expressions(rhs, op, self)

    def _new_unop(self, op):
        op_mapping = self._get_reverse_operator_mapping()
        if op not in op_mapping:
            raise ValueError('illegal operator: "{}"'.format(op))

        new_op = ast.UnaryOp(op=op_mapping[op](), operand=copy.copy(self.tree))
        return HDLExpression(ast.Expression(body=new_op))

    def __int__(self):
        """Alias for evaluate."""
        return self.evaluate()

    def __truth__(self):
        """Boolean value."""
        return bool(self.evaluate() != 0)

    def __bool__(self):
        """Boolean."""
        return self.__truth__()

    def __add__(self, other):
        """Add expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return self._new_binop("+", other)

    def __radd__(self, other):
        """Add expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as left-hand side
        """
        return self._new_binop("+", other, this_lhs=False)

    def __sub__(self, other):
        """Subtract expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return self._new_binop("-", other)

    def __rsub__(self, other):
        """Subtract expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as left-hand side
        """
        return self._new_binop("-", other, this_lhs=False)

    def __mul__(self, other):
        """Multiply expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return self._new_binop("*", other)

    def __rmul__(self, other):
        """Multiply expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as left-hand side
        """
        return self._new_binop("*", other, this_lhs=False)

    def __truediv__(self, other):
        """Divide expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return self._new_binop("/", other)

    def __lshift__(self, val):
        """Shift operator."""
        return self._new_binop("<<", val, this_lhs=True)

    def __rshift__(self, val):
        """Shift operator."""
        return self._new_binop(">>", val, this_lhs=True)

    def __or__(self, other):
        """Bitwise OR."""
        return self._new_binop("|", other, this_lhs=True)

    def __ror__(self, other):
        """Reverse Bitwise OR."""
        return self._new_binop("|", other, this_lhs=False)

    def __and__(self, other):
        """Bitwise AND."""
        return self._new_binop("&", other, this_lhs=True)

    def __rand__(self, other):
        """Reverse Bitwise AND."""
        return self._new_binop("&", other, this_lhs=False)

    def __xor__(self, other):
        """Bitwise XOR."""
        return self._new_binop("^", other, this_lhs=True)

    def __rxor__(self, other):
        """Reverse Bitwise XOR."""
        return self._new_binop("^", other, this_lhs=False)

    def __invert__(self):
        """Bitwise negation."""
        return self._new_unop("~")

    def bool_neg(self):
        """Boolean negation."""
        return self._new_unop("!")

    def bool_and(self, other):
        """Boolean AND."""
        return self._new_binop("&&", other)

    def bool_or(self, other):
        """Boolean OR."""
        return self._new_binop("||", other)

    def __eq__(self, other):
        """Comparison."""
        return self._new_binop("==", other)

    def __ne__(self, other):
        """Not equal."""
        return self._new_binop("!=", other)

    def __gt__(self, other):
        """Greater than."""
        return self._new_binop(">", other)

    def __lt__(self, other):
        """Less than."""
        return self._new_binop("<", other)

    def __ge__(self, other):
        """Greater or equal."""
        return self._new_binop(">=", other)

    def __le__(self, other):
        """Less or equal."""
        return self._new_binop("=<", other)

    def reduce_expr(self):
        """Reduce expression without evaluating."""
        new_tree = self._reduce_binop(self.tree.body)

        # replace tree
        self.tree.body = new_tree

    @staticmethod
    def _reduce_binop(binop):
        if not isinstance(binop, ast.BinOp):
            raise TypeError("only BinOp allowed")

        # unwrap Expressions
        if isinstance(binop.right, ast.Expression):
            right = binop.right.body
        else:
            right = binop.right

        if isinstance(binop.left, ast.Expression):
            left = binop.left.body
        else:
            left = binop.left

        # BinOp recursion
        if isinstance(right, ast.BinOp):
            right = HDLExpression._reduce_binop(right)

        if isinstance(left, ast.BinOp):
            left = HDLExpression._reduce_binop(left)

        if isinstance(
            binop.op,
            (ast.Add, ast.Sub, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor),
        ):
            if isinstance(left, ast.Num):
                prune_left = bool(left.n == 0)
            else:
                prune_left = False

            if isinstance(right, ast.Num):
                prune_right = bool(right.n == 0)
            else:
                prune_right = False
        elif isinstance(binop.op, (ast.Mult, ast.Div)):
            if isinstance(left, ast.Num):
                if left.n == 0:
                    return ast.Num(n=0)
                prune_left = bool(left.n == 1)
            else:
                prune_left = False

            if isinstance(right, ast.Num):
                if right.n == 0:
                    if isinstance(right, ast.Mult):
                        return ast.Num(n=0)
                    else:
                        raise ValueError("division by zero")
                prune_right = bool(right.n == 1)
            else:
                prune_right = False
        else:
            prune_left = False
            prune_right = False

        # prune
        if prune_left is True and prune_right is True:
            # doesn't do anything
            return ast.Num(n=0)
        elif prune_left is True:
            return right
        elif prune_right is True:
            return left
        else:
            return ast.BinOp(left, binop.op, right)
