"""VCD Dump Generator."""

from ..abshdl.codegen import HDLCodeGenerator
from datetime import datetime


class VCDGenerator(HDLCodeGenerator):
    """Make dumps."""

    def __init__(self, **kwargs):
        """Initialize."""
        self.elements = []

    def add_elements(self, *elements):
        """Add elements."""
        self.elements.extend(elements)

    def gen_VCDDump(self, element, **kwargs):
        """Dump VCD dump descriptor."""
        ret_str = ''
        ret_str += '$date\n {} \n$end\n'.format(datetime.now())
        ret_str += '$version hdltools VCDGenerator $end\n'
        ret_str += '$timescale {} $end'.format(element.timescale) + '\n'
        ret_str += '$scope module {} $end\n'.format(element.name)
        for identifier, var in element.variables.items():
            ret_str += self.dump_element(var, identifier=identifier) + '\n'

        ret_str += '$upscope $end\n'
        ret_str += '$enddefinitions $end\n'

        # dump initial
        ret_str += '#0\n$dumpvars\n'
        for name, value in element.initial.items():
            ret_str += '{}{}\n'.format(value,
                                       element.variable_identifiers[name])
        ret_str += '$end\n'
        for step, changes in enumerate(element.vcd):
            if len(changes) == 0:
                continue
            ret_str += '#{}\n'.format(step+1)
            for name, value in changes.items():
                ret_str += '{}{}\n'.format(value,
                                           element.variable_identifiers[name])

        ret_str += '$dumpoff\n'
        for name, value in element.initial.items():
            ret_str += 'x{}\n'.format(element.variable_identifiers[name])
        ret_str += '$end'

        return ret_str

    def gen_VCDVariable(self, element, **kwargs):
        """Dump variable."""
        ret_str = '$var {} {} {} {} $end'.format(element.var_type,
                                                 element.size,
                                                 kwargs['identifier'],
                                                 *element.identifiers)
        return ret_str
