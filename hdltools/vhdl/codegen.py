"""Generate VHDL code."""

import math
from ..abshdl.codegen import HDLCodeGenerator, indent


class VHDLCodeGenerator(HDLCodeGenerator):
    """Generate VHDL code."""

    VHDL_PORT_DIRECTION = ['in', 'out', 'inout']
    VHDL_SIGNAL_TYPE = ['signal']

    def gen_HDLModulePort(self, element, **kwargs):
        """Generate ports."""
        if 'evaluate' in kwargs:
            evaluate = kwargs['evaluate']
        else:
            evaluate = False

        vec = self.dump_element(element.vector,
                                evaluate=evaluate)

        if element.direction == 'in':
            port_direction = 'in'
        elif element.direction == 'out':
            port_direction = 'out'
        elif element.direction == 'inout':
            port_direction = 'inout'
        else:
            raise ValueError('invalid port type: {}'.format(element.direction))

        # use std_logic by default
        if 'port_type' in kwargs:
            port_type = kwargs.pop('port_type')
        else:
            port_type = 'std_logic'

        if vec is not None:
            ext_str = vec
            port_type += '_vector'
        else:
            ext_str = ''

        if 'last' in kwargs:
            last = kwargs.pop('last')
        else:
            last = False

        ret_str = '{} : {} {}{}'.format(element.name,
                                        port_direction,
                                        port_type,
                                        ext_str)

        if last is False:
            ret_str += ';'

        return ret_str

    def gen_HDLMacro(self, element, **kwargs):
        """Generate constants."""
        value = self.dump_element(element.value, **kwargs)

        if 'const_type' in kwargs:
            const_type = kwargs.pop('const_type')
        else:
            # integer by default
            const_type = 'integer'

        ret_str = 'constant {} : {} := {};'.format(element.name,
                                                   const_type,
                                                   value)
        return ret_str

    def gen_HDLConcatenation(self, element, **kwargs):
        """Concatenations."""
        ret_str = '({})'.format(
            ','.join([self.dump_element(x) for x in element.items]))
        return ret_str

    def gen_HDLSwitch(self, element, **kwargs):
        """Switch / case."""
        ret_str = 'case {} is\n'.format(self.dump_element(element.switch,
                                                          evaluate=False))

        for name, case in element.cases.items():
            ret_str += self.dump_element(case,
                                         evaluate=False)

        ret_str += '\nend case;'
        return ret_str

    def gen_HDLCase(self, element, **kwargs):
        """Case."""
        ret_str = 'when {} =>'.format(self.dump_element(element.case_value,
                                                        format='int'))
        ret_str += self.dump_element(element.scope)
        return ret_str

    def gen_HDLModule(self, element, **kwargs):
        """Generate module."""
        ret_str = ''
        for constant in element.constants:
            ret_str += self.dump_element(constant) + '\n'
        ret_str += 'entity {} is\n'.format(element.name)
        if len(element.parameters) > 0:
            ret_str += 'generic('
            ret_str += ';\n'.join([self.dump_element(p, last=True)
                                   for p in element.parameters])
            ret_str += ');'
        if len(element.ports) > 0:
            ret_str += 'port('
            ret_str += ';\n'.join([self.dump_element(p, last=True)
                                  for p in element.ports])
            ret_str += ');'

        ret_str += 'end {};\n'.format(element.name)

        if 'arch_name' in kwargs:
            arch_name = kwargs.pop('arch_name')
        else:
            arch_name = 'DEFAULT'

        ret_str += 'architecture {} of {} is\n'.format(arch_name, element.name)
        ret_str += 'begin\n'
        ret_str += self.dump_element(element.scope)
        ret_str += 'end {}\n'.format(arch_name)

    def gen_HDLComment(self, element, **kwargs):
        """Generate comment."""
        return '--{}'.format(element.text)

    def gen_HDLMultiLineComment(self, element, **kwargs):
        """Generate multi-line comments."""
        return '\n'.join(['--{}'.format(line)
                          for line in element.text.split('\n')])
