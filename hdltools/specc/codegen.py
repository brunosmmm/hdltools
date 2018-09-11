"""HDLTools IR -> SpecC code generator."""

from ..abshdl.codegen import HDLCodeGenerator
from scoff.codegen import indent


class SpecCCodeGenerator(HDLCodeGenerator):
    """Generate SpecC code."""

    def gen_HDLModuleTypedPort(self, element, **kwargs):
        """Generate behavior ports."""
        ret_str = '{} {} {}'.format(element.direction,
                                    element.signal.var_type,
                                    element.name)

        return ret_str

    def gen_HDLModuleParameter(self, element, **kwargs):
        """Parameters are not supported."""
        self._unsupported_class(element)

    def gen_HDLSensitivityDescriptor(self, element, **kwargs):
        """Not supported."""
        self._unsupported_class(element)

    def gen_HDLSensitivityList(self, element, **kwargs):
        """Not supported."""
        self._unsupported_class(element)

    def _unsupported_class(self, element):
        """Classes which are not supported."""
        raise TypeError('{} not supported in SpecC'
                        .format(element.__class__.__name__))

    def gen_HDLModule(self, element, **kwargs):
        """Translate HDLModule to behavior."""
        ret_str = ''
        # insert defines
        for constant in element.constants:
            ret_str += self.dump_element(constant) + '\n'

        ret_str += 'behavior {}('.format(element.name)

        # ports
        if len(element.ports) > 0:
            ret_str += ', '.join([self.dump_element(p) for p in element.ports])

        # close port description
        ret_str += ')\n{\n'

        # what is main scope? main function or overall?
        ret_str += self.dump_element(element.scope)

        # close behavior scope
        ret_str += '\n}'

        return ret_str

    @indent
    def gen_HDLScope(self, element, **kwargs):
        """Generate scopes."""
        print([x for x in element])
        return ''
