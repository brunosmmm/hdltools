"""Generate HDL from stimulus models (when possible)."""

from . import HDLSimulationObject
from ..abshdl import HDLObject
from ..abshdl.signal import HDLSignal
from ..abshdl.highlvl import HDLBlock
import ast
import inspect
import textwrap
import astunparse


class IllegalCodeError(Exception):
    """Illegal code, untranslatable."""

    pass


class CombinatorialChecker(ast.NodeVisitor):
    """Checks if the logic is purely combinatorial."""

    def __init__(self, obj, if_seq=True):
        """Initialize."""
        # internal state
        self._state = "normal"
        self._assign_target = None
        self._is_comb = True
        self._assign_target_list = []
        self._if_seq = if_seq
        self._inferred_sequential_blocks = []

        # get source, parse
        self.sim_obj = obj
        self.logic_src = inspect.getsource(obj.logic)
        self.tree = ast.parse(textwrap.dedent(self.logic_src), mode="exec")
        self.visit(self.tree)

    def _record_assignment(
        self, assign_node, infer_register=False, assign=None
    ):
        """Record assignment."""
        if isinstance(assign_node, ast.Attribute):
            # "globals"
            if assign_node.attr in self._assign_target_list:
                raise IllegalCodeError(
                    "line {}: port / inferred register "
                    "cannot be assigned "
                    "more than once in a cycle.".format(assign_node.lineno)
                )
            self._assign_target_list.append(
                [assign_node.attr, "global", infer_register, assign]
            )
        elif isinstance(assign_node, ast.Name):
            self._assign_target_list.append(
                [assign_node.id, "local", False, assign]
            )
        else:
            raise TypeError(
                "unsupported type for assignment: {}".format(
                    assign_node.__class__.__name__
                )
            )

    def visit_If(self, node, manual_visit=False, if_level=0):
        """Visit an If node."""
        prev_state = self._state
        self._state = "ifelse"
        if self._if_seq is True:
            # do not analyze if statements. Ony IfExp will be considered
            # concurrent.
            self._is_comb = False

            if if_level == 0:
                # ignore sequential inferring.
                # visit node.test manually
                if isinstance(node.test, ast.Call):
                    # check if we are calling rising_edge or falling_edge
                    if isinstance(node.test.func, ast.Attribute):
                        if (
                            node.test.func.value.id == "self"
                            and node.test.func.attr
                            in ["rising_edge", "falling_edge"]
                        ):
                            # will infer a sequential block
                            self._inferred_sequential_blocks.append(
                                [node.test.func.attr, node.test.args, node.body]
                            )
                        else:
                            raise IllegalCodeError(
                                "unknown function: {}".format(
                                    node.test.func.attr
                                )
                            )
                    else:
                        raise IllegalCodeError("function calls not allowed")
                elif isinstance(node.test, ast.Compare):
                    # infer sensitivity list
                    self._inferred_sequential_blocks.append(
                        [None, node.test, node.body]
                    )
                else:
                    raise IllegalCodeError(
                        "cannot infer sequential block: " "unsupported pattern"
                    )

            # visit children manually
            for child in node.body:
                if isinstance(child, ast.If):
                    # visit manually.
                    self.visit_If(
                        child, manual_visit=True, if_level=if_level + 1
                    )
                else:
                    self.visit(child)

            if if_level > 0:
                for child in node.orelse:
                    if isinstance(child, ast.If):
                        self.visit_If(
                            child, manual_visit=True, if_level=if_level + 1
                        )
                    else:
                        self.visit(child)
            else:
                if len(node.orelse) > 0:
                    raise IllegalCodeError(
                        "top-level if cannot have else clause"
                    )

            self._state = prev_state
            return

        if_assigned_stmts = []
        else_assigned_stmts = []
        # visit manually
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                if_assigned_stmts.extend(
                    self.visit_Assign(stmt, manual_visit=True)
                )
            elif isinstance(stmt, ast.If):
                if_assigned_stmts.extend(self.visit_If(stmt, manual_visit=True))
            else:
                self.visit(stmt)

        # handle else
        for stmt in node.orelse:
            if isinstance(stmt, ast.Assign):
                else_assigned_stmts.extend(
                    self.visit_Assign(stmt, manual_visit=True)
                )
            elif isinstance(stmt, ast.If):
                else_assigned_stmts.extend(
                    self.visit_If(stmt, manual_visit=True)
                )
            else:
                self.visit(stmt)

        # detect ilegalities
        if_global_names = [x.attr for x in if_assigned_stmts]
        else_global_names = [x.attr for x in else_assigned_stmts]

        for name in if_global_names:
            if if_global_names.count(name) > 1:
                raise IllegalCodeError(
                    "port / inferred register "
                    "cannot be assigned "
                    "more than once in a cycle."
                )

        for name in else_global_names:
            if else_global_names.count(name) > 1:
                raise IllegalCodeError(
                    "port / inferred register "
                    "cannot be assigned "
                    "more than once in a cycle."
                )

        # add up assignments and register them
        assignment_list = []
        assignment_record_list = []
        if_assigned_stmts.extend(else_assigned_stmts)
        for assignment in if_assigned_stmts:
            if assignment.attr not in assignment_list:
                assignment_list.append(assignment.attr)
                if manual_visit is False:
                    self._record_assignment(assignment)
                else:
                    assignment_record_list.append(assignment)

        self._state = prev_state
        if manual_visit is True:
            return assignment_record_list
        else:
            return None

    def visit_For(self, node):
        """Visit a for node."""
        self._is_comb = False
        self.generic_visit(node)

    def visit_BinOp(self, node):
        """Visits a binary op."""
        self.generic_visit(node)

    def visit_Call(self, node):
        """Visits a function call."""
        func = node.func
        # detect an access to functions that imply sequential block
        if isinstance(func, ast.Attribute):
            if func.value.id == "self":
                if func.attr in HDLSimulationObject._sequential_methods:
                    self._is_comb = False
        self.generic_visit(node)

    def visit_Assign(self, node, manual_visit=False):
        """Visits an assignment."""
        # search for assignments that imply memory of past states.
        # obvious case: analog to an augmented assign.
        # local variables do not necessarily imply registers.
        # object attributes do imply registers, except for ports
        assigned_globals = []
        prev_state = self._state
        self._state = "assign"
        self._assign_target = node.targets
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                if target.value.id == "self":
                    if (
                        target.attr in self.sim_obj._inputs
                        or target.attr in self.sim_obj._outputs
                    ):
                        # will not imply a register directly
                        # however, we must check
                        # base on current and last state
                        if prev_state == "ifelse":
                            # inside if statement
                            infer_register = True
                        else:
                            infer_register = False
                    else:
                        # will imply a register.
                        self._is_comb = False
                        infer_register = True
                    # record assignments of ports / globals
                    if manual_visit is False:
                        self._record_assignment(
                            target, infer_register, assign=node
                        )
                    else:
                        assigned_globals.append(target, infer_register)
            elif isinstance(target, ast.Name):
                # locals are taken as combinatorial assignments.
                # signal must be created before passing through
                # high level constructor. May be impossible to determine size!
                self._record_assignment(target, assign=node)

        self.generic_visit(node)
        self._state = prev_state
        if manual_visit is True:
            return assigned_globals
        else:
            return None

    def visit_Name(self, node):
        """Visit names."""
        if self._state == "normal":
            return
        elif self._state == "assign":
            # perform checking
            for target in self._assign_target:
                if isinstance(target, ast.Name):
                    if node != target:
                        # do not check a node against itself!
                        if node.id == target.id:
                            # memory. is sequential.
                            self._is_comb = False
                            break

    def visit_Attribute(self, node):
        """Visit attributes."""
        if self._state == "normal":
            return
        elif self._state == "assign":
            for target in self._assign_target:
                if isinstance(target, ast.Attribute):
                    if node != target:
                        if (
                            node.value.id == target.value.id
                            and node.attr == target.attr
                        ):
                            # memory.
                            self._is_comb = False
                            break

    def visit_AugAssign(self, node):
        """Visits an augmented assignment."""
        # augmented assignmens imply memory of a past state -> sequential
        if isinstance(node.value, ast.Attribute):
            if node.value.id == "self":
                self._is_comb = False
                self._record_assignment(node.value, True, assign=node)
        # gets ignored in local variables
        self.generic_visit(node)

    def is_combinatorial_only(self):
        """Get analysis result."""
        return self._is_comb

    def get_assigned_globals(self):
        """Get globals assigned (ports)."""
        return [
            (name, reg)
            for name, kind, reg, obj in self._assign_target_list
            if kind == "global"
        ]

    def get_assigned_locals(self):
        """Get local assigned (signals)."""
        return [
            name
            for name, kind, reg, obj in self._assign_target_list
            if kind == "local"
        ]

    def get_inferred_regs(self):
        """Get inferred registers."""
        infer = {}
        for name, scope, is_reg, obj in self._assign_target_list:
            if name in infer:
                if infer[name] is False and is_reg is True:
                    infer[name] = True
            else:
                infer[name] = is_reg

        return infer

    def get_inferred_combs(self):
        """Get inferred combinational signals."""
        infer = {}
        for name, scope, is_reg, obj in self._assign_target_list:
            if name in infer:
                if is_reg is True:
                    del infer[name]
            else:
                if is_reg is False:
                    infer[name] = obj

        return infer


class LegalityChecker(ast.NodeVisitor):
    """Check legality for transformation."""

    def __init__(self, obj):
        """Initialize."""
        self._is_legal = True
        self.tree = ast.parse(textwrap.dedent(obj), mode="exec")
        self.visit(self.tree)

    def visit_While(self, node):
        """Visit a while node."""
        self._is_legal = False
        self.generic_visit(node)

    def visit_Try(self, node):
        """Visit a try node."""
        self._is_legal = False
        self.generic_visit(node)

    def visit_TryFinally(self, node):
        """Visit try."""
        self._is_legal = False
        self.generic_visit(node)

    def visit_TryExcept(self, node):
        """Visit try."""
        self._is_legal = False
        self.generic_visit(node)

    def visit_Import(self, node):
        """Visit import statement."""
        self._is_legal = False
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Visit import statement."""
        self._is_legal = False
        self.generic_visit(node)

    def visit_With(self, node):
        """Visit with statement."""
        self._is_legal = False
        self.generic_visit(node)

    def visit_Delete(self, node):
        """Visit delete statement."""
        self._is_legal = False
        self.generic_visit(node)

    def visit_Return(self, node):
        """Visit return statement."""
        self._is_legal = False
        self.generic_visit(node)

    def visit_Yield(self, node):
        """Visit yield statement."""
        self._is_legal = False
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Visit class definition."""
        self._is_legal = False
        self.generic_visit(node)

    def is_legal(self):
        """Get legality."""
        return self._is_legal


class LogicSanitizer(ast.NodeTransformer):
    """Sanitize logic function."""

    def __init__(self, obj=None, insert_reg_list=None):
        """Initialize."""
        self._globals = set()
        self._obj = obj
        if insert_reg_list is None:
            self._proxy_list = []
        else:
            self._proxy_list = insert_reg_list
        if obj is not None:
            self.logic_src = inspect.getsource(self._obj.logic)
            self.tree = ast.parse(textwrap.dedent(self.logic_src), mode="exec")
            self.visit(self.tree)

    def apply_on_ast(self, tree):
        """Run on ast."""
        self.tree = tree
        self.visit(self.tree)

    def visit_Print(self, node):
        """Visit and remove print statements."""
        return None

    def visit_Raise(self, node):
        """Visit and remove raise statements."""
        return None

    def visit_Assert(self, node):
        """Visit and remove assert statements."""
        return None

    def visit_Attribute(self, node):
        """Remove attributes."""
        if node.value.id == "self":
            self._globals.add(node.attr)
            if node.attr in self._proxy_list:
                return ast.Name(id="reg_" + node.attr, ctx=node.ctx)
            else:
                return ast.Name(id=node.attr, ctx=node.ctx)

        return node

    def get_sanitized(self, unparse=False, rebuild=True):
        """Get sanitized tree."""
        # build exterior function
        if rebuild is True:
            arg_list = []
            for arg in self._globals:
                arg_list.append(ast.arg(arg, None))
            root_args = ast.arguments(arg_list, None, [], None, [], [])
            root = ast.FunctionDef(
                name=self._obj.identifier,
                args=root_args,
                body=self.tree.body[0].body,
            )
        else:
            root = self.tree

        if unparse is True:
            return astunparse.unparse(root)
        else:
            return root


class HDLSimulationObjectScheduler(HDLObject):
    """Schedule a simulation object."""

    def __init__(self, obj):
        """Initialize."""
        if not isinstance(obj, HDLSimulationObject):
            raise TypeError("only HDLSimulationObject allowed")

        self._obj = obj

    def schedule(self):
        """Do the scheduling."""
        # check various things
        src = inspect.getsource(self._obj.logic)

        # check legality
        if LegalityChecker(src).is_legal() is False:
            raise RuntimeError("Illegal code detected")

        # determine if it is puerely combinatorial
        comb_check = CombinatorialChecker(self._obj)
        comb_only = comb_check.is_combinatorial_only()

        # sanitize
        tree = LogicSanitizer(self._obj).get_sanitized()

        inputs = {
            inp.name: HDLSignal("comb", inp.name, inp.size)
            for name, inp in self._obj.inputs.items()
        }
        outputs = {
            out.name: HDLSignal("comb", out.name, out.size)
            for name, out in self._obj.outputs.items()
        }
        signals = {
            name: HDLSignal("comb", name)
            for name in comb_check.get_assigned_locals()
        }
        state = {
            name: HDLSignal("reg", var.name, var.size)
            for name, var in self._obj.state_elements.items()
        }

        signals.update(state)
        signals.update(inputs)
        signals.update(outputs)

        ports = {}
        ports.update(inputs)
        ports.update(outputs)

        if comb_only is True:
            # just generate a simple module
            # apply decorator
            tree.decorator_list = [
                ast.Call(
                    func=ast.Name(id="ParallelBlock", ctx=ast.Load()),
                    args=[],
                    keywords=[],
                    starargs=None,
                )
            ]

            # now use HDLBlock
            block = HDLBlock(**signals)
            block.apply_on_ast(tree)
            return block.get()
        else:
            # re-build combinational assignments
            comb_assignments = []
            for name, assign in comb_check.get_inferred_combs().items():
                comb_assignments.append(assign)
            # build inferred blocks
            block_num = 0
            sequential_blocks = []
            arg_list = []
            for name, signal in ports.items():
                arg_list.append(ast.arg(name, None))
            args = ast.arguments(arg_list, None, [], [], [], [])
            for edge, sig, body in comb_check._inferred_sequential_blocks:
                arg_list_inner = []
                for name, signal in signals.items():
                    if name != sig[0].s:
                        arg_list_inner.append(ast.arg(name, None))
                args_inner = ast.arguments(arg_list_inner, None, [], [], [], [])
                seqfn = ast.FunctionDef(
                    name="gen_{}".format(block_num),
                    args=args_inner,
                    body=body,
                    decorator_list=[
                        ast.Call(
                            func=ast.Name(id="SequentialBlock", ctx=ast.Load()),
                            args=[ast.Name(id=sig[0].s, ctx=ast.Load())],
                            keywords=[],
                            starargs=None,
                        )
                    ],
                    returns=None,
                )
                block_num += 1
                sequential_blocks.append(seqfn)

            # create proxy register assignments
            # TODO recover size
            inferred_regs = comb_check.get_inferred_regs()
            proxies = {
                "reg_" + name: HDLSignal("reg", "reg_" + name)
                for name, is_reg in inferred_regs.items()
                if is_reg is True
            }
            signals.update(proxies)

            # create ast items
            proxy_assignments = [
                ast.Assign(
                    targets=[ast.Name(id=name, ctx=ast.Store())],
                    value=ast.Name(id="reg_" + name, ctx=ast.Load()),
                )
                for name, is_reg in inferred_regs.items()
                if is_reg is True
            ]

            comb_assignments.extend(proxy_assignments)
            # add sequential blocks
            comb_assignments.extend(sequential_blocks)
            # top-level function
            topfn = ast.FunctionDef(
                name=self._obj.identifier,
                args=args,
                body=comb_assignments,
                decorator_list=[
                    ast.Call(
                        func=ast.Name(id="ParallelBlock", ctx=ast.Load()),
                        args=[],
                        keywords=[],
                        starargs=None,
                    )
                ],
            )

            block = HDLBlock(**signals)
            # sanitize (and insert proxies)
            tree = LogicSanitizer(
                insert_reg_list=[name for name, is_reg in inferred_regs.items()]
            )
            tree.apply_on_ast(topfn)
            final_ast = tree.get_sanitized(rebuild=False)
            # print(astunparse.unparse(final_ast))
            block.apply_on_ast(final_ast)
            return block.get()
