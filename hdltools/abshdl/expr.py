"""HDL Expressions."""

from . import HDLValue
from .const import HDLIntegerConstant
import hdltools.abshdl.signal as signal
import ast
import operator as op
import copy


class HDLExpression(HDLValue):
    """An expression involving parameters."""

    _ast_op_names = {ast.Sub: '-',
                     ast.Add: '+',
                     ast.Mult: '*',
                     ast.Div: '/',
                     ast.LShift: '<<',
                     ast.RShift: '>>',
                     ast.BitOr: '|',
                     ast.BitAnd: '&',
                     ast.BitXor: '^'}
    _operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                  ast.Div: op.truediv, ast.Pow: op.pow,
                  ast.USub: op.neg, ast.LShift: op.lshift,
                  ast.RShift: op.rshift, ast.BitOr: op.or_,
                  ast.BitAnd: op.and_, ast.BitXor: op.xor}

    def __init__(self, value):
        """Initialize.

        Args
        ----
        expr_tree: ast.Expression
            Expression tree
        """
        super(HDLExpression, self).__init__()
        if isinstance(value, str):
            self.tree = ast.parse(value, mode='eval')
            self.size = None
        elif isinstance(value, ast.Expression):
            self.tree = value
            self.size = None
        elif isinstance(value, HDLIntegerConstant):
            self.tree = ast.Expression(body=ast.Num(n=value.value))
            self.size = len(value)
        elif isinstance(value, int):
            self.tree = ast.Expression(body=ast.Num(n=value))
            self.size = HDLIntegerConstant.minimum_value_size(value)
        elif isinstance(value, signal.HDLSignal):
            self.tree = ast.Expression(body=ast.Name(id=value.name))
            self.size = len(value)
        elif isinstance(value, signal.HDLSignalSlice):
            name = ast.Name(id=value.signal.name)
            if len(value.vector) > 1:
                _slice = ast.Slice(upper=value.vector.left_size.tree,
                                   lower=value.vector.right_size.tree,
                                   step=None)
            else:
                _slice = ast.Index(value=value.vector.left_size.tree)
            self.tree = ast.Expression(body=ast.Subscript(value=name,
                                                          slice=_slice))
            self.size = len(value)
        else:
            raise TypeError('invalid type provided')

    def __len__(self):
        """Get width, if known."""
        if self.size is None:
            raise ValueError('cannot determine total length')
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
        elif isinstance(node, ast.BinOp):
            return self._operators[type(node.op)](self._evaluate(node.left,
                                                                 **kwargs),
                                                  self._evaluate(node.right,
                                                                 **kwargs))
        elif isinstance(node, ast.UnaryOp):
            return self._operators[type(node.op)](self._evaluate(node.operand,
                                                                 **kwargs))
        elif isinstance(node, ast.Call):
            if node.func.id in kwargs:
                # evaluate arguments
                arg_eval = []
                for arg in node.args:
                    arg_eval.append(self._evaluate(arg, **kwargs))

                return kwargs[node.func.id].call(*arg_eval, **kwargs)
            else:
                raise KeyError('function "{}" not'
                               ' available'.format(node.func.id))
        elif isinstance(node, ast.Subscript):
            signal_name = self._evaluate(node.value)
            _slice = self._evaluate(node.slice)
            # return string only
            return signal_name+_slice
        elif isinstance(node, ast.Index):
            return '[{}]'.format(self._evaluate(node.value))
        elif isinstance(node, ast.Slice):
            return '[{}:{}]'.format(self._evaluate(node.upper),
                                    self._evaluate(node.lower))

        else:
            raise TypeError(node)

    def _get_expr(self, node):
        # TODO: eliminate unnecessary parentheses
        if isinstance(node, ast.Expression):
            return self._get_expr(node.body)
        elif isinstance(node, ast.BinOp):
            left_expr = self._get_expr(node.left)
            right_expr = self._get_expr(node.right)

            return '({}{}{})'.format(left_expr,
                                     self._ast_op_names[node.op.__class__],
                                     right_expr)
        elif isinstance(node, ast.Num):
            return str(node.n)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            arg_list = []
            for arg in node.args:
                arg_list.append(self._get_expr(arg))
            return '{}({})'.format(node.func.id,
                                   ','.join(arg_list))
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
        if not isinstance(lhs, HDLExpression) or\
           not isinstance(rhs, HDLExpression):
            raise TypeError('can only combine two HDLExpression objects')

        # check operator?
        op_mapping = cls._get_reverse_operator_mapping()
        if op not in op_mapping:
            raise ValueError('illegal operator: "{}"'.format(op))

        new_op = ast.BinOp(left=copy.copy(lhs.tree),
                           op=op_mapping[op](),
                           right=copy.copy(rhs.tree))
        return HDLExpression(ast.Expression(body=new_op))

    def _new_binop(self, op, other, this_lhs=True):
        if isinstance(other, HDLExpression):
            rhs = other
        elif isinstance(other, HDLIntegerConstant):
            rhs = HDLExpression(other)
        elif isinstance(other, int):
            rhs = HDLExpression(other)
        else:
            raise TypeError('illegal type: "{}"'.format(type(rhs)))
        # create new BinOp
        if this_lhs is True:
            return self.combine_expressions(self, op, rhs)
        else:
            return self.combine_expressions(rhs, op, self)

    def __int__(self):
        """Alias for evaluate."""
        return self.evaluate()

    def __add__(self, other):
        """Add expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return self._new_binop('+', other)

    def __radd__(self, other):
        """Add expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as left-hand side
        """
        return self._new_binop('+', other, this_lhs=False)

    def __sub__(self, other):
        """Subtract expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return self._new_binop('-', other)

    def __rsub__(self, other):
        """Subtract expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as left-hand side
        """
        return self._new_binop('-', other, this_lhs=False)

    def __mul__(self, other):
        """Multiply expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return self._new_binop('*', other)

    def __rmul__(self, other):
        """Multiply expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as left-hand side
        """
        return self._new_binop('*', other, this_lhs=False)

    def __truediv__(self, other):
        """Divide expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return self._new_binop('/', other)

    def __lshift__(self, val):
        """Shift operator."""
        return self._new_binop('<<', val, this_lhs=True)

    def __rshift__(self, val):
        """Shift operator."""
        return self._new_binop('>>', val, this_lhs=True)

    def __or__(self, other):
        """Bitwise OR."""
        return self._new_binop('|', other, this_lhs=True)

    def __ror__(self, other):
        """Reverse Bitwise OR."""
        return self._new_binop('|', other, this_lhs=False)

    def __and__(self, other):
        """Bitwise AND."""
        return self._new_binop('&', other, this_lhs=True)

    def __rand__(self, other):
        """Reverse Bitwise AND."""
        return self._new_binop('&', other, this_lhs=False)

    def __xor__(self, other):
        """Bitwise XOR."""
        return self._new_binop('^', other, this_lhs=True)

    def __rxor__(self, other):
        """Reverse Bitwise XOR."""
        return self._new_binop('^', other, this_lhs=False)

    def reduce_expr(self):
        """Reduce expression without evaluating."""
        new_tree = self._reduce_binop(self.tree.body)

        # replace tree
        self.tree.body = new_tree

    @staticmethod
    def _reduce_binop(binop):
        if not isinstance(binop, ast.BinOp):
            raise TypeError('only BinOp allowed')

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

        if isinstance(binop.op, (ast.Add, ast.Sub,
                                 ast.LShift, ast.RShift,
                                 ast.BitOr, ast.BitXor)):
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
                        raise ValueError('division by zero')
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
