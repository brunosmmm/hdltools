"""Generate Verilog Statements."""

import math
from ..abshdl.codegen import HDLCodeGenerator


class VerilogCodeGenerator(HDLCodeGenerator):
    """Generate verilog code."""

    VERILOG_CONSTANT_RADIX = ['d', 'b', 'h']
    VERILOG_PORT_DIRECTION = ['in', 'out', 'inout']
    VERILOG_SIGNAL_TYPE = ['wire', 'reg']

    def gen_HDLModulePort(self, element, **kwargs):
        """Generate port."""
        return self.dumps_port(element.direction,
                               element.name,
                               element.vector.evaluate())

    def gen_HDLIntegerConstant(self, element, **kwargs):
        """Generate an integer constant."""
        # check for format
        if 'radix' in kwargs:
            radix = kwargs['radix']
        else:
            radix = 'b'

        # check for size
        if 'size' in kwargs:
            size = kwargs['size']
        else:
            size = 32

        return self.dumps_vector(element.evaluate(),
                                 size,
                                 radix)

    def gen_HDLMacro(self, element, **kwargs):
        """Generate a define."""
        value = self.dump_element(element.value, **kwargs)
        return self.dumps_define(element.name, value)

    def gen_HDLSignal(self, element, **kwargs):
        """Generate signals."""
        if element.sig_type == 'comb':
            st = 'wire'
        elif element.sig_type == 'reg':
            st = 'reg'

        _slice = self.dump_element(element.vector)

        sig_decl = True
        if 'assign' in kwargs:
            sig_decl = not kwargs['assign']

        if sig_decl:
            return '{} {} {};'.format(st, _slice, element.name)
        else:
            return '{}'.format(element.name)

    def gen_HDLSignalSlice(self, element, **kwargs):
        """Generate sliced signal."""
        kwargs.update({'assign': True})
        signal = self.dump_element(element.signal, **kwargs)
        slic = self.dump_element(element.vector)

        return '{}{}'.format(signal, slic)

    def gen_HDLVectorDescriptor(self, element, **kwargs):
        """Generate a vector slice."""
        return self.dumps_extents(*element.evaluate())

    def gen_HDLAssignment(self, element, **kwargs):
        """Generate assignments."""
        assign_lhs = self.dump_element(element.signal, assign=True)
        assign_rhs = self.dump_element(element.value, radix='h')
        assign_type = element.get_assignment_type()
        if assign_type == 'parallel':
            assign_str = 'assign {} = {};'.format(assign_lhs,
                                                  assign_rhs)
        elif assign_type == 'series':
            if element.assign_type == 'block':
                assign_op = '<='
            else:
                assign_op = '='
            assign_str = '{} {} {};'.format(assign_lhs,
                                            assign_op,
                                            assign_rhs)
        return assign_str

    def gen_HDLExpression(self, element, **kwargs):
        """Get an expression."""
        return element.dumps()

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
