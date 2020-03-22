"""Trigger condition mini-language."""

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

    def visit_TriggerCondition(self, node):
        """Visit trigger condition."""
        name = node.sig.split("::")[-1]
        scope = "::".join(node.sig.split("::")[:-1])
        cond = VCDTriggerDescriptor(scope, name, node.value)
        self._conditions.append(cond)

    def visit_ConditionRight(self, node):
        """Visit rhs of statement."""
        if node.op != "&&":
            raise VisitError("only && operator supported")

    def get_conditions(self):
        """Get conditions."""
        return self._conditions


def parse_trigcond(text):
    """Parse vecgen file."""
    model = OBJDUMP_METAMODEL.model_from_str(text)
    return model


def build_descriptors_from_str(cond):
    """Build list of trigger descriptors from string."""
    ast = parse_trigcond(cond)
    visitor = TriggerConditionVisitor()
    visitor.visit(ast)
    return visitor.get_conditions()
