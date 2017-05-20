"""Generate Verilog Statements."""

import math
from ..codegen import HDLCodeGenerator


class VerilogCodeGenerator(HDLCodeGenerator):
    """Generate verilog code"""

    VERILOG_CONSTANT_RADIX = ['d', 'b', 'h']
    VERILOG_PORT_DIRECTION = ['in', 'out', 'inout']
    VERILOG_SIGNAL_TYPE = ['wire', 'reg']

    def gen_HDLModulePort(self, element, **kwargs):
        """Generate port."""
        return self.dumps_port(element.direction,
                               element.name,
                               element.vector.evaluate())

    @staticmethod
    def dumps_define(name, value):
        """Dump a define macro."""
        return '`define {} {}'.format(name, value)

    @staticmethod
    def dumps_vector(value, width, radix='h'):
        """Dump a verilog constant."""
        if radix not in VerilogCodeGenerator.VERILOG_CONSTANT_RADIX:
            raise ValueError('illegal constant type')

        # check if width can hold value
        if value > int(math.pow(2, float(width)) - 1):
            raise ValueError('requested width cannot hold passed value; '
                             '{} bits needed at least'.format(
                                 int(math.ceil(math.log2(value)))+1))

        ret_str = '{}\'{}'.format(str(width), radix)

        if radix == 'h':
            fmt_str = '{{:0{}X}}'.format(int(width/4))
            ret_str += fmt_str.format(value)
        elif radix == 'd':
            ret_str += str(value)
        elif radix == 'b':
            fmt_str = '{{:0{}b}}'.format(width)
            ret_str += fmt_str.format(value)

        return ret_str

    @staticmethod
    def dumps_extents(left, right):
        """Dump a vector extents."""
        return '[{}:{}]'.format(left, right)

    @staticmethod
    def dumps_port(direction, name, extents, last_port=False):
        """Dump port declation."""
        if direction not in VerilogCodeGenerator.VERILOG_PORT_DIRECTION:
            raise ValueError('illegal port direction: "{}"'.format(direction))
        if direction == 'in':
            port_direction = 'input'
        elif direction == 'out':
            port_direction = 'output'
        else:
            port_direction = direction
        if extents is not None:
            ext_str = VerilogCodeGenerator.dumps_extents(*extents)
        else:
            ext_str = ''
        ret_str = '{} {} {}'.format(port_direction, ext_str, name)
        if last_port is False:
            ret_str += ','

        return ret_str

    @staticmethod
    def dumps_signal(sig_type, name, extents):
        """Dump signal declaration (simple)."""
        pass
