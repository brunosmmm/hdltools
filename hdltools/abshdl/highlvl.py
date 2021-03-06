"""High-level coding using python syntax to build HDL structures."""

import inspect
import ast
import textwrap
import sys
import re
from collections import deque
from hdltools.abshdl import HDLObject
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.signal import HDLSignal, HDLSignalSlice
from hdltools.abshdl.port import HDLModulePort
from hdltools.abshdl.assign import HDLAssignment, HDLLazyValue
from hdltools.abshdl.ifelse import HDLIfElse, HDLIfExp
from hdltools.hdllib.patterns import (
    ClockedBlock,
    ClockedRstBlock,
    ParallelBlock,
    SequentialBlock,
)
from hdltools.hdllib.fsm import FSM
from hdltools.abshdl.concat import HDLConcatenation
from hdltools.abshdl.vector import HDLVectorDescriptor
from hdltools.abshdl.macro import HDLMacroValue


class PatternNotAllowedError(Exception):
    """Code pattern not allowed."""

    pass


class HDLPlaceholderSignal(HDLSignal):
    """Placeholder signal."""

    def __init__(self, *args, **kwargs):
        """Initialize."""
        super().__init__("other", *args, **kwargs)


class HDLBlock(HDLObject, ast.NodeVisitor):
    """Build HDL blocks from python syntax."""

    _CUSTOM_TYPE_MAPPING = {}
    _PATTERN_NAMES = [
        "ClockedBlock",
        "ClockedRstBlock",
        "ParallelBlock",
        "SequentialBlock",
        "HDLBlock",
    ]

    def __init__(self, mod=None, symbols=None, **kwargs):
        """Initialize."""
        super().__init__()
        self._init()

        # build internal signal scope
        self.signal_scope = {}
        if mod is not None:
            self._add_to_scope(**mod.get_signal_scope())
            self._hdlmod = mod
        self._add_to_scope(**kwargs)
        if symbols is None:
            self._symbols = {}
        else:
            self._symbols = symbols
        self.fsms = {}

    def _init(self):
        """Initialize or re-initialize."""
        self.scope = None
        self.current_scope = None
        self.block = None
        self.consts = None
        self._current_block = deque()
        self._current_block_kwargs = {}
        self._verify_signal_name = True

    def __call__(self, fn):
        """Decorate."""

        def wrapper_BlockBuilder(*args, **kwargs):
            self._init()
            self._build(fn, fn_kwargs=kwargs)
            return self.get()

        return wrapper_BlockBuilder

    def apply_on_ast(self, tree):
        """Do procedures directly on AST."""
        self.tree = tree
        self.visit(self.tree)

    def _signal_lookup(self, sig_name):
        """Signal lookup."""
        if isinstance(sig_name, int):
            return sig_name
        if self.signal_scope is not None:
            if sig_name in self.signal_scope:
                if isinstance(
                    self.signal_scope[sig_name], HDLPlaceholderSignal
                ):
                    # go find actual signal
                    # FIXME: should return a flag indicating placeholder
                    return self._current_block_kwargs[sig_name]
                return self.signal_scope[sig_name]
            else:
                return None
        else:
            # search in globals
            if sig_name in globals():
                return globals()[sig_name]
            else:
                return None

    def _build(self, target, fn_kwargs):
        for kwarg in fn_kwargs.values():
            if not isinstance(
                kwarg, (HDLSignal, HDLSignalSlice, HDLModulePort, int)
            ):
                raise RuntimeError(
                    "block kwargs must be of HDLSignal, HDLSignalSlice, "
                    "HDLModulePort or integer type"
                )
        self._current_block_kwargs = fn_kwargs
        src = inspect.getsource(target)
        self.tree = ast.parse(textwrap.dedent(src), mode="exec")
        self.visit(self.tree)

    def visit_FunctionDef(self, node):
        """Visit function declaration."""
        # starting point is function declaration. Remove our own decorator.
        decorator_list = [
            x
            for x in node.decorator_list
            if x.func.id != self.__class__.__name__
        ]
        if len(decorator_list) == 0:
            raise RuntimeError(
                "must be used in conjunction with a HDL block"
                " decorator, like ClockedBlock, ParallelBlock"
            )
        for decorator in decorator_list:
            try:
                decorator_class = getattr(
                    sys.modules[__name__], decorator.func.id
                )
            except:
                if decorator.func.id not in self._CUSTOM_TYPE_MAPPING:
                    decorator_class = None
                else:
                    decorator_class = self._CUSTOM_TYPE_MAPPING[
                        decorator.func.id
                    ]
            if decorator.func.id == "SequentialBlock":
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
            elif decorator.func.id in ("ClockedBlock", "ClockedRstBlock"):
                # a clocked block.
                # rebuild args
                args = []
                for arg in decorator.args:
                    _arg = self._signal_lookup(arg.id)
                    if _arg is None:
                        continue
                    args.append(_arg)
                if decorator.func.id == "ClockedBlock":
                    block = ClockedBlock.get(*args)
                else:
                    block = ClockedRstBlock.get(*args)
                if self.block is None:
                    self.block = block
                    self.scope = self.block.scope
                    self.current_scope = self.scope
                else:
                    self.scope.add(block)
                    self.current_scope = block.scope
            elif decorator.func.id == "ParallelBlock":
                block = ParallelBlock.get()
                if self.block is None:
                    self.block = block
                    self.scope = self.block
                    self.current_scope = self.scope
                else:
                    self.block.add(block)
                    self.current_scope = block
            elif decorator_class is not None and issubclass(
                decorator_class, FSM
            ):

                if node.name in self.fsms:
                    raise PatternNotAllowedError(
                        "FSM '{}' already declared.".format(node.name)
                    )
                # rebuild args
                args = []
                for arg in decorator.args:
                    _arg = self._signal_lookup(arg.id)
                    if _arg is None:
                        continue
                    args.append(_arg)
                kwargs = {}
                for kw in decorator.keywords:
                    if isinstance(kw.value, ast.Str):
                        kwargs[kw.arg] = kw.value.s
                # add signal scope in the mix
                kwargs["_signal_scope"] = self.signal_scope
                kwargs["instance_name"] = node.name
                block, const, fsm = decorator_class.get(*args, **kwargs)
                # perform checks
                state_var = fsm.state_var_name
                for fsm_name, _fsm in self.fsms.items():
                    if _fsm.state_var_name.name == state_var.name:
                        raise PatternNotAllowedError(
                            "state variable '{}' re-utilized in FSM '{}'".format(
                                node.name
                            )
                        )
                self.fsms[node.name] = fsm
                # go out of tree
                fsm = FSMBuilder(block, self.signal_scope)
                fsm._build(decorator_class)
                if self.block is None:
                    self.block = block
                    self.scope = self.block
                    self.current_scope = self.scope
                else:
                    self.block.add(block)
                    self.current_scope = block
                if self.consts is None:
                    self.consts = {c.name: c for c in const}
                else:
                    self.consts.update({c.name: c for c in const})

        # FIXME: this should probably come at the beginning
        if node.args.args is not None:
            for arg in node.args.args:
                if arg.arg not in self._current_block_kwargs:
                    raise RuntimeError(
                        f"while building  block: missing argument '{arg.arg}'"
                    )

        # enforce legality of scope
        if node.args.args is not None:
            scope_add = {
                arg.arg: HDLPlaceholderSignal(arg.arg, size=1)
                for arg in node.args.args
            }
            self._add_to_scope(**scope_add)
            # for arg in node.args.args:
            #     if arg.arg not in self.signal_scope:
            #         raise NameError(
            #             'in block declaration: "{}",'
            #             ' signal "{}" is not available'
            #             " in current module scope".format(node.name, arg.arg)
            #         )

        # push function name to stack
        self._current_block.append((node.name, self._current_block_kwargs))
        self.generic_visit(node)
        _, self._current_block_kwargs = self._current_block.pop()
        return node

    def visit_If(self, node):
        """Visit If statement."""
        self.visit(node.test)
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
                raise NameError(
                    'in "{}": signal "{}" not available in'
                    " current scope".format(
                        self._get_current_block(), node.value.id
                    )
                )
            if isinstance(node.slice, ast.Index):
                index = self.visit(node.slice.value)
                vec = HDLVectorDescriptor(index, index)
                return HDLSignalSlice(signal, vec)
            elif isinstance(node.slice, ast.Slice):
                if isinstance(node.slice.upper, ast.Constant):
                    upper = node.slice.upper.value
                else:
                    upper = node.slice.upper
                if isinstance(node.slice.lower, ast.Constant):
                    lower = node.slice.lower.value
                else:
                    lower = node.slice.lower
                return HDLSignalSlice(signal, [upper, lower])
            elif isinstance(node.slice, ast.Constant):
                if isinstance(node.slice.value, int):
                    vec = HDLVectorDescriptor(
                        node.slice.value, node.slice.value
                    )
                    return HDLSignalSlice(signal, vec)
                else:
                    raise TypeError(
                        "type {} not supported".format(
                            node.slice.value.__class__.__name__
                        )
                    )
            else:
                raise TypeError(
                    "type {} not supported".format(
                        node.slice.__class__.__name__
                    )
                )
        else:
            raise TypeError(
                "type {} not supported".format(node.value.__class__.__name__)
            )

    def visit_Constant(self, node):
        """Visit Constant."""
        if isinstance(node.value, int):
            return HDLExpression(node.value)
        return node

    def visit_Name(self, node):
        """Visit Name."""
        signal = self._signal_lookup(node.id)
        if signal is not None:
            if isinstance(signal, HDLSignalSlice):
                signal_name = signal.signal.name
            elif isinstance(signal, (HDLSignal, HDLModulePort)):
                signal_name = signal.name
            elif isinstance(signal, int):
                signal_name = signal
            else:
                raise RuntimeError("unknown error")
        else:
            signal_name = node.id
        if self._verify_signal_name:
            if signal is None:
                raise NameError("unknown name: {}".format(node.id))
        node.id = signal_name
        return HDLExpression(signal_name)

    def visit_Assign(self, node):
        """Visit Assignments."""
        self.generic_visit(node)
        assignments = []
        # check assignees (targets)
        assignees = []
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                # attributes are not allowed, except for self access
                if target.value.id == "self":
                    # bypass attribute access directly,
                    # later on we can execute the block itself in python
                    # if necessary
                    target.id = target.attr
                else:
                    raise PatternNotAllowedError(
                        "Attribute access is not allowed in HDL blocks."
                    )
            if self._signal_lookup(target.id) is None:
                if self._signal_lookup("reg_" + target.id) is None:
                    raise NameError(
                        'in "{}": signal "{}" not available in'
                        " current scope".format(
                            self._get_current_block(), target.id
                        )
                    )
                else:
                    target.id = "reg_" + target.id
            assignees.append(target.id)

        # check value assigned
        if isinstance(node.value, ast.Name):
            if self._signal_lookup(node.value.id) is None:
                raise NameError(
                    'in "{}": signal "{}" not available in'
                    " current scope".format(
                        self._get_current_block(), node.value.id
                    )
                )
            for assignee in assignees:
                assignments.append(
                    HDLAssignment(
                        self._signal_lookup(assignee),
                        self._signal_lookup(node.value.id),
                    )
                )
        elif isinstance(node.value, ast.Constant):
            for assignee in assignees:
                assignments.append(
                    HDLAssignment(
                        self._signal_lookup(assignee),
                        HDLExpression(node.value.value),
                    )
                )
        elif isinstance(node.value, (ast.List, ast.Tuple)):
            items = [self.visit(item) for item in node.value.elts]
            for assignee in assignees:
                assignments.append(
                    HDLAssignment(
                        self._signal_lookup(assignee),
                        HDLConcatenation(*items[::-1]),
                    )
                )
        elif isinstance(node.value, ast.Call):
            for assignee in assignees:
                args = [self._signal_lookup(arg.id) for arg in node.value.args]
                kwargs = {
                    kw.arg: self._signal_lookup(kw.value.id)
                    for kw in node.value.keywords
                }
                if node.value.func.id in self._symbols:
                    fn = self._symbols[node.value.func.id]
                    # generate
                    ret = fn(*args, **kwargs)
                else:
                    # dont do anything for now, lazy
                    fn = node.value.func.id
                    ret = (
                        HDLLazyValue(
                            fn,
                            fnargs=args,
                            fnkwargs=kwargs,
                        ),
                    )
                assignments.append(
                    HDLAssignment(self._signal_lookup(assignee), ret)
                )
        else:
            try:
                expr = self.visit(node.value)
                for assignee in assignees:
                    assignments.append(
                        HDLAssignment(self._signal_lookup(assignee), expr)
                    )
            except TypeError:
                # raise TypeError('type {} not supported'.format(
                #    node.value.__class__.__name__))
                raise
        # find out where to insert statement
        if len(assignments) > 0:
            self.current_scope.add(*assignments)

    def visit_Call(self, node):
        """Visit call."""
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in self._PATTERN_NAMES
        ):
            return
        self._verify_signal_name = True
        if (
            isinstance(node.func, ast.Name)
            and node.func.id not in self._symbols
            and node.func.id not in self._CUSTOM_TYPE_MAPPING
        ):
            # unless it is a callable object, in which case the name is here
            raise NameError(
                "unknown python function: '{}'".format(node.func.id)
            )
        # FIXME: disallow starred
        args = []
        for arg in node.args:
            if isinstance(arg, ast.Name):
                self.visit_Name(arg)
                args.append(self._signal_lookup(arg.id))
            else:
                args.append(arg)
        kwargs = {}
        for kwarg in node.keywords:
            if isinstance(kwarg.value, ast.Name):
                self.visit_Name(kwarg.value)
                kwargs[kwarg.arg] = self._signal_lookup(kwarg.value.id)
            else:
                kwargs[kwarg.arg] = kwarg.value
        # self._verify_signal_name = False

        # call?
        # fn = self._symbols[node.func.id]
        # ret = fn(*args, **kwargs)
        # return ret

    def visit_IfExp(self, node):
        """Visit If expression."""
        ifexp = HDLIfExp(
            self.visit(node.test),
            if_value=self.visit(node.body),
            else_value=self.visit(node.orelse),
        )
        self.generic_visit(node)
        return ifexp

    def visit_UnaryOp(self, node):
        """Visit Unary operations."""
        if isinstance(node.op, ast.Not):
            return HDLExpression(self.visit(node.operand)).bool_neg()
        elif isinstance(node.op, ast.Invert):
            return ~HDLExpression(self.visit(node.operand))
        else:
            raise TypeError(
                "operator {} not supported".format(node.op.__class__.__name__)
            )

    def visit_BinOp(self, node):
        """Visit Binary operations."""
        self.generic_visit(node)
        return HDLExpression(ast.Expression(body=node))

    def visit_Compare(self, node):
        """Visit Compare."""
        self.generic_visit(node)
        if isinstance(node.left, ast.Name):
            # NOTE: Don't know why this is necessary anymore
            left_sig = self._signal_lookup(node.left.id)
            if left_sig is None:
                if self._signal_lookup(node.left.id) is not None:
                    # rename
                    node.left.id = "reg_" + str(node.left.id)
                else:
                    raise NameError(
                        'in "{}": signal "{}" not available in'
                        " current scope".format(
                            self._get_current_block(), node.left.id
                        )
                    )
        if len(node.comparators) > 1:
            raise RuntimeError("only single comparison is allowed")
        (comp,) = node.comparators
        if isinstance(comp, ast.Name):
            comp_sig = self._signal_lookup(comp.id)
            if comp_sig is None:
                if self._signal_lookup("reg_" + str(comp.id)) is not None:
                    # is state register, rename
                    comp.id = "reg_" + str(comp.id)
                else:
                    raise NameError(
                        'in "{}": signal "{}" not available in'
                        " current scope".format(
                            self._get_current_block(), comp.id
                        )
                    )

        return HDLExpression(node)

    def visit_Expr(self, node):
        """Visit Expression."""
        self.generic_visit(node)
        return node

    def get(self):
        """Get block."""
        return (self.block, self.consts, self.fsms)

    def _get_current_block(self):
        try:
            block, kwargs = self._current_block.pop()
        except:
            return None

        self._current_block.append((block, kwargs))
        return block

    def _add_to_scope(self, **kwargs):
        """Add signals to internal scope."""
        for name, arg in kwargs.items():
            if isinstance(arg, (HDLSignal, HDLSignalSlice)):
                self.signal_scope[name] = arg

    @classmethod
    def add_custom_block(cls, block_class):
        """Add custom block class."""
        cls._CUSTOM_TYPE_MAPPING[block_class.__name__] = block_class


class FSMBuilder(HDLBlock):
    """Helper class that builds FSMs."""

    def __init__(self, fsm_block, signal_scope, **kwargs):
        """Initialize."""
        self._block = fsm_block
        super().__init__(**kwargs)
        self.signal_scope = signal_scope

    def _collect_states(self, cls):
        state_methods = {}
        for method_name, method in inspect.getmembers(cls):
            cls_name = cls.__name__
            m = re.match(
                r"_{}__state_([a-zA-Z0-9_]+)".format(cls_name), method_name
            )
            if m is not None:
                # found a state
                if inspect.ismethod(method) or inspect.isfunction(method):
                    args = set(inspect.getfullargspec(method).args)
                    input_list = args - set(["self"])
                    state_methods[m.group(1)] = (method, input_list)

        return state_methods

    def _build(self, target):
        self._class = target
        self._states = self._collect_states(target)
        super()._build(target, fn_kwargs={})

    def visit_FunctionDef(self, node):
        """Visit function (state definition)."""
        cls_name = self._class.__name__
        m = re.match(r"__state_([a-zA-Z0-9_]+)".format(cls_name), node.name)

        if m is not None:
            case_scope = self._block.find_by_tag(
                "__autogen_case_{}".format(m.group(1))
            )[0]
            if case_scope is None:
                raise RuntimeError("unknown error, cant find case scope")
            else:
                self.current_scope = case_scope

        self.generic_visit(node)

    def visit_Str(self, node):
        """Visit strings and guess state changes."""
        if self.current_scope is None:
            return None

        if node.s not in self._states:
            raise RuntimeError("invalid state: {}".format(node.s))

        return HDLMacroValue(node.s)

    def visit_Name(self, node):
        """Visit a name."""
        # why???
        if node.id in ("self", "FSM"):
            return
        if node.id not in self.signal_scope:
            raise NameError("unknown signal in FSM: '{}'".format(node.id))
