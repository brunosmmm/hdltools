"""Utility functions."""

import ast
import operator
from math import ceil, log


def clog2(value):
    """Get clog2."""
    return int(ceil(log(value, 2))) + 1


_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.FloorDiv: operator.floordiv,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval_math(expr_str):
    """Safely evaluate a math expression containing only numbers and arithmetic.

    Replaces unsafe eval() for user-provided size/template expressions.
    Only allows integer/float constants and basic arithmetic operators.
    """

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise ValueError(
                    f"unsupported constant type: {type(node.value).__name__}"
                )
            return node.value
        elif isinstance(node, ast.BinOp):
            if type(node.op) not in _SAFE_OPERATORS:
                raise ValueError(
                    f"unsupported operator: {type(node.op).__name__}"
                )
            return _SAFE_OPERATORS[type(node.op)](
                _eval(node.left), _eval(node.right)
            )
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in _SAFE_OPERATORS:
                raise ValueError(
                    f"unsupported operator: {type(node.op).__name__}"
                )
            return _SAFE_OPERATORS[type(node.op)](_eval(node.operand))
        else:
            raise ValueError(
                f"unsupported expression element: {type(node).__name__}"
            )

    tree = ast.parse(expr_str, mode="eval")
    return _eval(tree)
