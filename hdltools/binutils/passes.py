"""Visit and parse objdump."""

from scoff.ast.visits import ASTVisitor
from hdltools.binutils.instruction import AsmInstruction
from hdltools.binutils.function import AsmFunction


class AsmDumpPass(ASTVisitor):
    """Visit objdump output."""

    def __init__(self):
        """Initialize."""
        self._visited = False
        super().__init__()
        self._fn_locs = {}
        self._fn_by_name = {}

    def visit_Function(self, node):
        """Visit function."""
        self._fn_locs[node.header.symbol.name] = int(node.header.addr, 16)
        self._fn_by_name[node.header.symbol.name] = AsmFunction(
            node.header.symbol.name,
            int(node.header.addr, 16),
            node.instructions,
        )

    def visit_Instruction(self, node):
        """Visit instruction."""
        return AsmInstruction(
            int(node.addr, 16),
            int(node.opcode, 16),
            node.asm_txt.replace("\t", " "),
            node.parent,
        )

    def get_functions(self):
        """Get functions."""
        return self._fn_by_name

    def get_main(self):
        """Get main function."""
        if not self._visited:
            raise RuntimeError("visit has not occurred yet")
        return self._fn_by_name["main"]

    def get_entry_point(self):
        """Get entry point."""
        if not self._visited:
            raise RuntimeError("visit has not occurred yet")
        return self._fn_by_name["_start"]

    def visit(self, node):
        """Visit."""
        self._visited = False
        super().visit(node)
        self._visited = True
