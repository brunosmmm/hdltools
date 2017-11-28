"""HDL Code generation."""

from scoff.codegen import CodeGenerator
from .stmt import HDLStatement


class HDLCodeGenerator(CodeGenerator):
    """HDL Code generator."""

    def _check_validity(self, element):
        if isinstance(element, HDLStatement):
            if element.is_legal() is False:
                return False

        return True
