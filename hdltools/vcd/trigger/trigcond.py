"""Trigger condition mini-language."""

import re
import pkg_resources
from textx.metamodel import metamodel_from_file
from scoff.ast.visits import ASTVisitor, VisitError
from hdltools.vcd.trigger import VCDTriggerDescriptor

METAMODEL_FILE = pkg_resources.resource_filename(
    "hdltools", "vcd/trigger/trigcond.tx"
)
OBJDUMP_METAMODEL = metamodel_from_file(METAMODEL_FILE)


class TriggerConditionVisitor(ASTVisitor):
    """Trigger condition ast visitor."""

    def __init__(self):
        """Initialize."""
        super().__init__()
        self._conditions = []
        self._mode = None

    @staticmethod
    def get_slice_size(node):
        """Get slice size."""
        if hasattr(node, "right") and node.right is not None:
            return abs(node.left - node.right.val) + 1
        return 1

    @staticmethod
    def get_signal_size(node):
        """Get slice size."""
        if hasattr(node, "right") and node.right is not None:
            return abs(node.left - node.right.val) + 1
        return node.left

    def visit_TriggerCondition(self, node):
        """Visit trigger condition."""
        name = node.sig.name.split("::")[-1]
        scope = "::".join(node.sig.name.split("::")[:-1])
        if hasattr(node.sig, "slice") and node.sig.slice is not None:
            # create pattern with many don't cares
            m = re.match(r"[01xX]+", node.value)
            if m is None:
                raise RuntimeError("only binary is supported if using slices")
            pattern_len = len(node.value)
            slice_len = self.get_slice_size(node.sig.slice)
            if pattern_len != slice_len:
                raise RuntimeError(
                    f"pattern length error: expected {slice_len}, got {pattern_len}"
                )
            pattern = ["x" for _ in range(self.get_signal_size(node.sig.size))]
            invert_bit_order = False
            if (
                hasattr(node.sig.slice, "right")
                and node.sig.slice.right is not None
            ):
                bits = range(node.sig.slice.right.val, node.sig.slice.left + 1)
                if node.sig.slice.right.val < node.sig.slice.left:
                    bits = list(
                        range(
                            node.sig.slice.right.val, node.sig.slice.left + 1
                        )
                    )
                    invert_bit_order = True
                else:
                    bits = list(
                        range(
                            node.sig.slice.left, node.sig.slice.right.val + 1
                        )
                    )
                for i in bits:
                    if invert_bit_order:
                        pattern[i] = node.value[len(node.value) - i - 1]
                    else:
                        pattern[i] = node.value[i]
            else:
                pattern[node.sig.slice.left] = node.value

            # respect bit order
            if (
                hasattr(node.sig.size, "right")
                and node.sig.size.right is not None
                and node.sig.size.right.val < node.sig.size.left
            ):
                pattern = pattern[::-1]

            # create pattern with x's
            pattern = "".join(pattern)
        else:
            pattern = node.value

        cond = VCDTriggerDescriptor(scope, name, pattern)
        self._conditions.append(cond)

    def visit_SignalDescriptor(self, node):
        """Visit signal descriptor."""
        if hasattr(node, "slice") and node.slice is not None:
            if not hasattr(node, "size") or node.size is None:
                raise RuntimeError(
                    "signal with slice must have size descriptor"
                )
        else:
            return node

        if hasattr(node.slice, "right") and node.slice.right is not None:
            slice_size = abs(node.slice.left - node.slice.right.val) + 1
            if node.slice.right.val < node.size.right.val:
                raise RuntimeError("slicing error")
        else:
            slice_size = 1
        if node.slice.left > node.size.left:
            raise RuntimeError("slicing error")
        if hasattr(node.size, "right") and node.size.right is not None:
            sig_size = abs(node.size.left - node.size.right.val) + 1
        else:
            sig_size = node.size.left
        if slice_size > sig_size:
            raise RuntimeError("slice is wider than signal width")
        return node

    def visit_ConditionRight(self, node):
        """Visit rhs of statement."""
        if self._mode is None:
            if node.op == "&&":
                self._mode = "&&"
            elif node.op == "=>":
                self._mode = "=>"
            else:
                raise RuntimeError("only && or => operators supported for now")
        else:
            if node.op != self._mode:
                raise RuntimeError("all operators must be homonegeous")

    def get_conditions(self):
        """Get conditions."""
        return self._conditions

    def get_mode(self):
        """Get operation mode."""
        return self._mode

    def visit(self, node):
        """Visit."""
        super().visit(node)
        # default mode
        if self._mode is None:
            self._mode = "&&"


def parse_trigcond(text):
    """Parse vecgen file."""
    model = OBJDUMP_METAMODEL.model_from_str(text)
    return model


def build_descriptors_from_str(cond):
    """Build list of trigger descriptors from string."""
    ast = parse_trigcond(cond)
    visitor = TriggerConditionVisitor()
    visitor.visit(ast)
    return (visitor.get_conditions(), visitor.get_mode())
