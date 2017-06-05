"""Generate HDL from stimulus models (when possible)."""

from . import HDLSimulationObject
from ..abshdl import HDLObject
from ..abshdl.expr import HDLExpression
from ..abshdl.seq import HDLSequentialBlock
from ..hdllib.patterns import get_module, ParallelBlock
from ..abshdl.signal import HDLSignal
from ..abshdl.highlvl import HDLBlock
import ast
import inspect
import textwrap
from astdump import indented


class IllegalCodeError(Exception):
    """Illegal code, untranslatable."""

    pass


class CombinatorialChecker(ast.NodeVisitor):
    """Checks if the logic is purely combinatorial."""

    def __init__(self, obj, if_seq=True):
        """Initialize."""
        # internal state
        self._state = 'normal'
        self._assign_target = None
        self._is_comb = True
        self._assign_target_list = []
        self._if_seq = if_seq

        # get source, parse
        self.sim_obj = obj
        self.logic_src = inspect.getsource(obj.logic)
        self.tree = ast.parse(textwrap.dedent(self.logic_src), mode='exec')
        self.visit(self.tree)

    def _record_assignment(self, assign_node):
        """Record assignment."""
        if isinstance(assign_node, ast.Attribute):
            # "globals"
            if assign_node.attr in self._assign_target_list:
                raise IllegalCodeError('line {}: port / inferred register '
                                       'cannot be assigned '
                                       'more than once in a cycle.'
                                       .format(assign_node.lineno))
        self._assign_target_list.append(assign_node.attr)

    def visit_If(self, node, manual_visit=False):
        """Visit an If node."""
        if self._if_seq is True:
            # do not analyze if statements. Ony IfExp will be considered
            # concurrent.
            self._is_comb = False
            return
        if_assigned_stmts = []
        else_assigned_stmts = []
        prev_state = self._state
        self._state = 'ifelse'
        # visit manually
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                if_assigned_stmts.extend(
                    self.visit_Assign(stmt,
                                      manual_visit=True))
            elif isinstance(stmt, ast.If):
                if_assigned_stmts.extend(
                    self.visit_If(stmt,
                                  manual_visit=True))
            else:
                self.visit(stmt)

        # handle else
        for stmt in node.orelse:
            if isinstance(stmt, ast.Assign):
                else_assigned_stmts.extend(
                    self.visit_Assign(stmt,
                                      manual_visit=True))
            elif isinstance(stmt, ast.If):
                else_assigned_stmts.extend(
                    self.visit_If(stmt,
                                  manual_visit=True))
            else:
                self.visit(stmt)

        # detect ilegalities
        if_global_names = [x.attr for x in if_assigned_stmts]
        else_global_names = [x.attr for x in else_assigned_stmts]

        for name in if_global_names:
            if if_global_names.count(name) > 1:
                raise IllegalCodeError('port / inferred register '
                                       'cannot be assigned '
                                       'more than once in a cycle.')

        for name in else_global_names:
            if else_global_names.count(name) > 1:
                raise IllegalCodeError('port / inferred register '
                                       'cannot be assigned '
                                       'more than once in a cycle.')

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
            if func.value.id == 'self':
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
        self._state = 'assign'
        self._assign_target = node.targets
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                if target.value.id == 'self':
                    if target.attr in self.sim_obj._inputs or\
                       target.attr in self.sim_obj._outputs:
                        # will not imply a register directly
                        # however, we must check
                        pass
                    else:
                        # will imply a register.
                        self._is_comb = False
                        break
                    # record assignments of ports / globals
                    if manual_visit is False:
                        self._record_assignment(target)
                    else:
                        assigned_globals.append(target)
            elif isinstance(target, ast.Name):
                # a local variable. check if implies register
                # must visit child nodes.
                pass

        self.generic_visit(node)
        self._state = prev_state
        if manual_visit is True:
            return assigned_globals
        else:
            return None

    def visit_Name(self, node):
        """Visit names."""
        if self._state == 'normal':
            return
        elif self._state == 'assign':
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
        if self._state == 'normal':
            return
        elif self._state == 'assign':
            for target in self._assign_target:
                if isinstance(target, ast.Attribute):
                    if node != target:
                        if node.value.id == target.value.id and\
                           node.attr == target.attr:
                            # memory.
                            self._is_comb = False
                            break

    def visit_AugAssign(self, node):
        """Visits an augmented assignment."""
        # augmented assignmens imply memory of a past state -> sequential
        if isinstance(node, ast.Attribute):
            if node.value.id == 'self':
                self._is_comb = False
        # gets ignored in local variables
        self.generic_visit(node)

    def is_combinatorial_only(self):
        """Get analysis result."""
        return self._is_comb


class LegalityChecker(ast.NodeVisitor):
    """Check legality for transformation."""

    def __init__(self, obj):
        """Initialize."""
        self._is_legal = True
        self.tree = ast.parse(textwrap.dedent(obj), mode='exec')
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

    def __init__(self, obj):
        """Initialize."""
        self._globals = set()
        self._obj = obj
        self.logic_src = inspect.getsource(self._obj.logic)
        self.tree = ast.parse(textwrap.dedent(self.logic_src), mode='exec')
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
        if node.value.id == 'self':
            self._globals.add(node.attr)
            return ast.Name(id=node.attr,
                            ctx=node.ctx)

        return node

    def get_sanitized(self):
        """Get sanitized tree."""
        # build exterior function
        arg_list = []
        for arg in self._globals:
            arg_list.append(ast.arg(arg, None))
        root_args = ast.arguments(arg_list, None, [], None, [], [])
        root = ast.FunctionDef(name=self._obj.identifier,
                               args=root_args,
                               body=self.tree.body[0].body)
        return root


class HDLSimulationObjectScheduler(HDLObject):
    """Schedule a simulation object."""

    def __init__(self, obj):
        """Initialize."""
        if not isinstance(obj, HDLSimulationObject):
            raise TypeError('only HDLSimulationObject allowed')

        self._obj = obj

    def schedule(self):
        """Do the scheduling."""
        # check various things
        src = inspect.getsource(self._obj.logic)

        # check legality
        if LegalityChecker(src).is_legal() is False:
            raise RuntimeError('Illegal code detected')

        # determine if it is puerely combinatorial
        comb_only = CombinatorialChecker(self._obj).is_combinatorial_only()

        # sanitize
        tree = LogicSanitizer(self._obj).get_sanitized()

        if comb_only is True:
            # just generate a simple module
            print('Function is combinatorial')
            # create signals
            inputs = {inp.name: HDLSignal('comb', inp.name, inp.size)
                      for name, inp in self._obj.report_inputs().items()}
            outputs = {out.name: HDLSignal('comb', out.name, out.size)
                       for name, out in self._obj.report_outputs().items()}

            # apply decorator
            tree.decorator_list = [ast.Call(func=ast.Name(id='ParallelBlock',
                                                          ctx=ast.Load()),
                                            args=[],
                                            keywords=[],
                                            starargs=None)]

            # now use HDLBlock
            inputs.update(outputs)
            block = HDLBlock(**inputs)
            block.apply_on_ast(tree)
            print(block.get())

        else:
            print('Function has sequential elements')
