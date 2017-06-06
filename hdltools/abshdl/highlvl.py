"""High-level coding using python syntax to build HDL structures."""

import inspect
import ast
import textwrap
from . import HDLObject
from .expr import HDLExpression
from .signal import HDLSignal, HDLSignalSlice
from .assign import HDLAssignment
from .ifelse import HDLIfElse, HDLIfExp
from ..hdllib.patterns import ClockedBlock, ParallelBlock, SequentialBlock
from .concat import HDLConcatenation
from .vector import HDLVectorDescriptor


class HDLBlock(HDLObject, ast.NodeVisitor):
    """Build HDL blocks from python syntax."""

    def __init__(self, **kwargs):
        """Initialize."""
        super(HDLBlock, self).__init__()
        self._init()

        # build internal signal scope
        self.signal_scope = {}
        for name, arg in kwargs.items():
            if isinstance(arg, (HDLSignal, HDLSignalSlice)):
                self.signal_scope[name] = arg

    def _init(self):
        """Initialize or re-initialize."""
        self.scope = None
        self.current_scope = None
        self.block = None

    def __call__(self, fn):
        """Decorate."""
        def wrapper_BlockBuilder(*args):
            self._init()
            self._build(fn)
            return self.get()
        return wrapper_BlockBuilder

    def apply_on_ast(self, tree):
        """Do procedures directly on AST."""
        self.tree = tree
        self.visit(self.tree)

    def _signal_lookup(self, sig_name):
        """Signal lookup."""
        if self.signal_scope is not None:
            if sig_name in self.signal_scope:
                return self.signal_scope[sig_name]
            else:
                return None
        else:
            # search in globals
            if sig_name in globals():
                return globals()[sig_name]
            else:
                return None

    def _build(self, target):
        src = inspect.getsource(target)
        self.tree = ast.parse(textwrap.dedent(src), mode='exec')
        self.visit(self.tree)

    def visit_FunctionDef(self, node):
        """Visit function declaration."""
        # starting point is function declaration. Remove our own decorator.
        decorator_list = [x for x in node.decorator_list if x.func.id !=
                          self.__class__.__name__]
        if len(decorator_list) == 0:
            raise RuntimeError('must be used in conjunction with a HDL block'
                               ' decorator, like ClockedBlock, ParallelBlock')
        for decorator in decorator_list:
            if decorator.func.id == 'SequentialBlock':
                # sequential block.
                args = []
                for arg in decorator.args:
                    _arg = self._signal_lookup(arg.id)
                    if _arg is None:
                        continue
                    args.append(_arg)
                block = SequentialBlock.get(*args)
                if self.block is None:
                    self.block = block
                    self.scope = self.block.scope
                    self.current_scope = self.scope
                else:
                    self.scope.add(block)
                    self.current_scope = block.scope
            elif decorator.func.id == 'ClockedBlock':
                # a clocked block.
                # rebuild args
                args = []
                for arg in decorator.args:
                    _arg = self._signal_lookup(arg.id)
                    if _arg is None:
                        continue
                    args.append(_arg)
                block = ClockedBlock.get(*args)
                if self.block is None:
                    self.block = block
                    self.scope = self.block.scope
                    self.current_scope = self.scope
                else:
                    self.scope.add(block)
                    self.current_scope = block.scope
            elif decorator.func.id == 'ParallelBlock':
                block = ParallelBlock.get()
                if self.block is None:
                    self.block = block
                    self.scope = self.block
                    self.current_scope = self.scope
                else:
                    self.block.add(block)
                    self.current_scope = block
        self.generic_visit(node)
        return node

    def visit_If(self, node):
        """Visit If statement."""
        ifelse = HDLIfElse(HDLExpression(ast.Expression(body=node.test)))
        self.current_scope.add([ifelse])
        last_scope = self.current_scope

        # ordered visit, two scopes, so separe
        self.current_scope = ifelse.if_scope
        for _node in node.body:
            self.visit(_node)
        self.current_scope = ifelse.else_scope
        for _node in node.orelse:
            self.visit(_node)
        self.current_scope = last_scope
        return node

    def visit_Subscript(self, node):
        """Visit Subscripts."""
        if isinstance(node.value, ast.Name):
            signal = self._signal_lookup(node.value.id)
            if signal is None:
                raise KeyError('signal not found')
            if isinstance(node.slice, ast.Index):
                index = self.visit(node.slice.value)
                vec = HDLVectorDescriptor(index, index)
                return HDLSignalSlice(signal,
                                      vec)
            elif isinstance(node.slice, ast.Slice):
                if isinstance(node.slice.upper, ast.Num):
                    upper = node.slice.upper.n
                else:
                    upper = node.slice.upper
                if isinstance(node.slice.lower, ast.Num):
                    lower = node.slice.lower.n
                else:
                    lower = node.slice.lower
                return HDLSignalSlice(signal,
                                      [upper,
                                       lower])
            else:
                raise TypeError('type {} not supported'.format(
                    node.slice.__class__.__name__))
        else:
            raise TypeError('type {} not supported'.format(
                node.value.__class__.__name__))

    def visit_Num(self, node):
        """Visit Num."""
        return HDLExpression(node.n)

    def visit_Name(self, node):
        """Visit Name."""
        return HDLExpression(node.id)

    def visit_Assign(self, node):
        """Visit Assignments."""
        assignments = []
        # check assignees (targets)
        assignees = []
        for target in node.targets:
            if self._signal_lookup(target.id) is None:
                raise KeyError('signal "{}" was not found'.format(target.id))
            assignees.append(target.id)

        # check value assigned
        if isinstance(node.value, ast.Name):
            if self._signal_lookup(node.value.id) is None:
                raise KeyError('signal "{}" was not found'.format(
                    node.value.id))
            for assignee in assignees:
                assignments.append(
                    HDLAssignment(self._signal_lookup(assignee),
                                  self._signal_lookup(node.value.id)))
        elif isinstance(node.value, ast.Num):
            for assignee in assignees:
                assignments.append(
                    HDLAssignment(self._signal_lookup(assignee),
                                  HDLExpression(node.value.n)))
        elif isinstance(node.value, (ast.List, ast.Tuple)):
            items = [self.visit(item) for item in node.value.elts]
            for assignee in assignees:
                assignments.append(
                    HDLAssignment(self._signal_lookup(assignee),
                                  HDLConcatenation(*items[::-1])))
        else:
            try:
                expr = self.visit(node.value)
                for assignee in assignees:
                    assignments.append(
                        HDLAssignment(self._signal_lookup(assignee),
                                      expr))
            except TypeError:
                # raise TypeError('type {} not supported'.format(
                #    node.value.__class__.__name__))
                raise
        # find out where to insert statement
        self.current_scope.add(*assignments)

    def visit_IfExp(self, node):
        """Visit If expression."""
        ifexp = HDLIfExp(HDLExpression(ast.Expression(body=node.test)),
                         if_value=self.visit(node.body),
                         else_value=self.visit(node.orelse))
        return ifexp

    def visit_UnaryOp(self, node):
        """Visit Unary operations."""
        if isinstance(node.op, ast.Not):
            return HDLExpression(self.visit(node.operand)).bool_neg()
        elif isinstance(node.op, ast.Invert):
            return ~HDLExpression(self.visit(node.operand))
        else:
            raise TypeError('operator {} not supported'.
                            format(node.op.__class__.__name__))

    def visit_BinOp(self, node):
        """Visit Binary operations."""
        return HDLExpression(ast.Expression(body=node))

    def get(self):
        """Get block."""
        if self.block is not None:
            return self.block
