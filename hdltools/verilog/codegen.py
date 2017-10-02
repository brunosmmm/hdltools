"""Generate Verilog Statements."""

import math
from ..abshdl.codegen import HDLCodeGenerator, indent
from ..abshdl.const import HDLIntegerConstant

_INDENT_STR = '    '


class VerilogCodeGenerator(HDLCodeGenerator):
    """Generate verilog code."""

    VERILOG_CONSTANT_RADIX = ['d', 'b', 'h']
    VERILOG_PORT_DIRECTION = ['in', 'out', 'inout']
    VERILOG_SIGNAL_TYPE = ['wire', 'reg']

    def gen_HDLModulePort(self, element, **kwargs):
        """Generate port."""
        if 'evaluate' in kwargs:
            evaluate = kwargs['evaluate']
        else:
            evaluate = False

        if element.vector is None:
            _slice = ''
        else:
            size = None
            try:
                size = len(element.vector)
            except:
                pass

            if size == 1:
                _slice = ''
            else:
                _slice = self.dump_element(element.vector,
                                           evaluate=evaluate)

        return self.dumps_port(element.direction,
                               element.name,
                               _slice,
                               **kwargs)

    def gen_HDLIntegerConstant(self, element, **kwargs):
        """Generate an integer constant."""
        # check for format
        if 'radix' in kwargs:
            radix = kwargs['radix']
        elif 'radix' in element.optional_args:
            radix = element.optional_args['radix']
        else:
            radix = 'b'

        # check for size
        if 'size' in kwargs:
            size = kwargs['size']
        else:
            size = element.size

        if 'no_size' in kwargs:
            no_size = kwargs.pop('no_size')
        elif 'no_size' in element.optional_args:
            no_size = element.optional_args.pop('no_size')
        else:
            no_size = False

        if no_size is False:
            return self.dumps_vector(element.evaluate(),
                                     size,
                                     radix)
        else:
            return str(element.evaluate())

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
        elif element.sig_type == 'const':
            st = 'localparam'
        elif element.sig_type == 'var':
            st = 'integer'

        if element.vector is None:
            _slice = ''
        else:
            size = None
            try:
                size = len(element.vector)
            except:
                pass

            if size == 1:
                _slice = ''
            else:
                _slice = self.dump_element(element.vector)

        sig_decl = True
        if 'assign' in kwargs:
            sig_decl = not kwargs['assign']

        if sig_decl:
            ret_str = '{} {} {}'.format(st, _slice, element.name)
            if element.sig_type == 'const':
                ret_str += ' = {};'.format(self.dump_element(
                    element.default_val,
                    format='int'))
            else:
                ret_str += ';'
            return ret_str
        else:
            return '{}'.format(element.name)

    def gen_HDLSignalSlice(self, element, **kwargs):
        """Generate sliced signal."""
        kwargs.update({'assign': True})
        signal = self.dump_element(element.signal, **kwargs)
        slic = self.dump_element(element.vector, simplify_extents=True)

        return '{}{}'.format(signal, slic)

    def gen_HDLVectorDescriptor(self, element, **kwargs):
        """Generate a vector slice."""
        if 'evaluate' in kwargs:
            evaluate = kwargs.pop('evaluate')
        else:
            evaluate = False

        if evaluate is True:
            extents = element.evaluate()
        else:
            extents = element.get_bounds()
        kwargs['part_select'] = element.part_select
        if element.part_select is True:
            extents = (extents[0], element.part_select_length)
        return self.dumps_extents(*extents, **kwargs)

    def gen_HDLAssignment(self, element, **kwargs):
        """Generate assignments."""
        assign_lhs = self.dump_element(element.signal, assign=True)
        if element.signal.get_sig_type() == 'var':
            assign_rhs = self.dump_element(element.value, no_size=True,
                                           assign=True)
        else:
            assign_rhs = self.dump_element(element.value, radix='h',
                                           assign=True)
        assign_type = element.get_assignment_type()

        if 'no_semi' in kwargs:
            no_semicolon = kwargs['no_semi']
        else:
            no_semicolon = False

        if assign_type == 'parallel':
            assign_str = 'assign {} = {}'.format(assign_lhs,
                                                 assign_rhs)
        elif assign_type == 'series':
            if element.assign_type == 'block':
                assign_op = '<='
            else:
                assign_op = '='
            assign_str = '{} {} {}'.format(assign_lhs,
                                           assign_op,
                                           assign_rhs)
        if no_semicolon is False:
            assign_str += ';'
        return assign_str

    def gen_HDLExpression(self, element, **kwargs):
        """Get an expression."""
        # insert more stuff into kwargs
        kwargs.update(element.optional_args)
        if 'format' in kwargs:
            fmt = kwargs.pop('format')
            if fmt == 'int':
                try:
                    return self.dump_element(
                        HDLIntegerConstant(element.evaluate(),
                                           element.size,
                                           **kwargs))
                except KeyError:
                    # tried to evaluate an expression which contains
                    # symbols.
                    pass

        # replace operators
        ret_str = element.dumps().replace('=<', '<=')
        # replace constants
        ret_str = ret_str.replace('True', '1')
        ret_str = ret_str.replace('False', '0')
        return ret_str

    def gen_HDLModuleParameter(self, element, **kwargs):
        """Generate Module parameter."""
        ret_str = 'parameter '
        if element.ptype is not None:
            ret_str += element.ptype + ' '

        sep_str = ','
        if 'last' in kwargs:
            if kwargs['last'] is True:
                sep_str = ''

        ret_str += element.name + ' '
        if element.value is not None:
            ret_str += '= {}{}'.format(self.dump_element(element.value),
                                       sep_str)
        else:
            ret_str += sep_str

        return ret_str

    def gen_HDLConcatenation(self, element, **kwargs):
        """Generate concatenation."""
        # force constants to be dumped with size
        if element.direction == 'rl':
            items = element.items[::-1]
        else:
            items = element.items
        ret_str = '{{{}}}'.format(
            ', '.join([self.dump_element(x, format='int')
                       for x in items]))

        return ret_str

    def gen_HDLIfElse(self, element, **kwargs):
        """Generate if-else statement."""
        ret_str = 'if ({}) begin\n'.format(
            self.dump_element(element.condition))
        ret_str += self.dump_element(element.if_scope)
        ret_str += '\nend'

        if len(element.else_scope):
            ret_str += '\nelse begin\n'
            ret_str += self.dump_element(element.else_scope)
            ret_str += '\nend'

        return ret_str

    def gen_HDLIfExp(self, element, **kwargs):
        """Generate one-line if-else."""
        ret_str = '({}) ? {} : {}'.format(
            self.dump_element(element.condition),
            self.dump_element(element.if_value),
            self.dump_element(element.else_value))
        return ret_str

    @indent
    def gen_HDLScope(self, element, **kwargs):
        """Generate several assignments."""
        test = [(x, self.dump_element(x)) for x in element]
        for x in test:
            if x[1] is None:
                raise Exception(x[0])
        return '\n'.join([self.dump_element(x) for x in element])

    def gen_HDLSensitivityDescriptor(self, element, **kwargs):
        """Generate always sensitivity elements."""
        if element.sens_type == 'rise':
            sens_str = 'posedge'
        elif element.sens_type == 'fall':
            sens_str = 'negedge'
        elif element.sens_type == 'both':
            raise ValueError('not synthesizable')
        elif element.sens_type == 'any':
            return '*'

        return sens_str+' {}'.format(self.dump_element(element.signal,
                                                       assign=True))

    def gen_HDLSensitivityList(self, element, **kwargs):
        """Generate always sensitivity list."""
        return '@({})'.format(','.join([self.dump_element(x) for
                                        x in element]))

    def gen_HDLSequentialBlock(self, element, **kwargs):
        """Generate always block."""
        if element.sens_list is None:
            sens_list = ''
        else:
            sens_list = self.dump_element(element.sens_list)
        ret_str = 'always {} begin\n'.format(sens_list)

        ret_str += self.dump_element(element.scope)
        ret_str += '\nend\n'

        return ret_str

    def gen_HDLModule(self, element, **kwargs):
        """Generate module declaration."""
        ret_str = ''
        for constant in element.constants:
            ret_str += self.dump_element(constant) + '\n'

        ret_str += 'module {}\n'.format(element.name)

        if len(element.params) > 0:
            ret_str += '#(\n'
            ret_str += ',\n'.join([self.dump_element(p, last=True) for
                                   p in element.params])
            ret_str += '\n)\n'

        ret_str += '(\n'
        if len(element.ports) > 0:
            ret_str += ',\n'.join([self.dump_element(p, last=True) for
                                   p in element.ports])

        ret_str += '\n);\n'

        # dump only declaration
        if 'decl_only' in kwargs:
            if kwargs['decl_only'] is True:
                return ret_str

        ret_str += self.dump_element(element.scope)

        ret_str += '\nendmodule\n'

        return ret_str

    def gen_HDLComment(self, element, **kwargs):
        """Generate single line comments."""
        return '//{}'.format(element.text)

    def gen_HDLMultiLineComment(self, element, **kwargs):
        """Generate multi line comments."""
        return '/* {} */'.format(element.text)

    def gen_HDLSwitch(self, element, **kwargs):
        """Generate case."""
        ret_str = 'case ({})\n'.format(self.dump_element(element.switch,
                                                         evaluate=False))
        for name, case in element.cases.items():
            ret_str += self.dump_element(case,
                                         evaluate=False)

        ret_str += '\nendcase\n'
        return ret_str

    def gen_HDLCase(self, element, **kwargs):
        """Generate one case."""
        ret_str = self.dump_element(element.case_value,
                                    format='int',
                                    radix='h') + ': begin\n'
        ret_str += self.dump_element(element.scope)
        ret_str += '\nend\n'

        return ret_str

    def gen_HDLForLoop(self, element, **kwargs):
        """Generate For Loop."""
        ret_str = 'for ({}; {}; {}) begin\n'.format(
            self.dump_element(element
                              .init,
                              no_semi=True),
            self.dump_element(element
                              .stop),
            self.dump_element(element.
                              after,
                              no_semi=True))
        ret_str += self.dump_element(element.scope)
        ret_str += '\nend\n'

        return ret_str

    def gen_HDLMacroValue(self, element, **kwargs):
        """Generate macro usage in code."""
        ret_str = '`{}'.format(element.name)
        return ret_str

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
    def dumps_extents(left, right, simplify_extents=True, part_select=False):
        """Dump a vector extents."""
        if repr(left) != repr(right) or simplify_extents is False:
            if part_select is False:
                return '[{}:{}]'.format(left, right)
            else:
                return '[{}{}:{}]'.format(left,
                                          '+' if right > 0 else '-',
                                          right)
        else:
            return '[{}]'.format(left)

    @staticmethod
    def dumps_port(direction, name, extents, last=False):
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
            ext_str = extents
        else:
            ext_str = ''
        ret_str = '{} {} {}'.format(port_direction, ext_str, name)
        if last is False:
            ret_str += ','

        return ret_str
