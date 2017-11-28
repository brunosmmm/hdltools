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

    # basic types to be implemented
    def gen_HDLIntegerConstant(self, element, **kwargs):
        """Generate Integer constants."""
        raise NotImplementedError

    def gen_HDLStringConstant(self, element, **kwargs):
        """Generate String constants."""
        raise NotImplementedError

    def gen_HDLVectorDescriptor(self, element, **kwargs):
        """Generate Vector elements."""
        raise NotImplementedError

    def gen_HDLModulePort(self, element, **kwargs):
        """Generate ports."""
        raise NotImplementedError
