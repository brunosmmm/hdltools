"""Generate Verilog Statements."""

import math

VERILOG_CONSTANT_RADIX = ['d', 'b', 'h']
VERILOG_PORT_DIRECTION = ['input', 'output', 'inout']


def dumps_define(name, value):
    """Dump a define macro."""
    return '`define {} {}'.format(name, value)


def dumps_vector(value, width, radix='h'):
    """Dump a verilog constant."""
    if radix not in VERILOG_CONSTANT_RADIX:
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


def dumps_extents(left, right):
    """Dump a vector extents."""
    return '[{}:{}]'.format(left, right)


def dumps_port(direction, name, extents, last_port=False):
    """Dump port declation."""
    if direction not in VERILOG_PORT_DIRECTION:
        raise ValueError('illegal port direction: "{}"'.format(direction))
    if extents is not None:
        ext_str = dumps_extents(*extents)
    else:
        ext_str = ''
    ret_str = '{} {} {}'.format(direction, ext_str, name)
    if last_port is False:
        ret_str += ','

    return ret_str
