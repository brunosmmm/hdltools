"""Memory mapped interface description parser."""

import pkg_resources
from textx.metamodel import metamodel_from_file
from hdltools.abshdl.registers import HDLRegister, HDLRegisterField
from hdltools.abshdl.port import HDLModulePort
from hdltools.abshdl.module import HDLModuleParameter
from hdltools.abshdl.const import HDLIntegerConstant, HDLStringConstant
from hdltools.abshdl.expr import HDLExpression

MMAP_COMPILER_GRAMMAR = pkg_resources.resource_filename(
    "hdltools", "mmap/mmap.tx"
)

MMAP_METAMODEL = metamodel_from_file(MMAP_COMPILER_GRAMMAR)


def bitfield_pos_to_slice(pos):
    """Convert to slice from parser object."""
    ret = [int(pos.left)]
    if pos.right is not None:
        ret.append(int(pos.right))

    return ret


def slice_size(slic):
    """Get slice size in bits."""
    if len(slic) > 1:
        return slic[0] - slic[1] + 1
    else:
        return 1


class FlagPort(HDLModulePort):
    """A port dependent on a register field."""

    def __init__(self, target_register, target_field, direction, name):
        """Initialize."""
        if target_field is not None:
            field = target_register.get_field(target_field)
            field_size = len(field.get_range())
        else:
            field_size = target_register.size
        self.target_register = target_register
        self.target_field = target_field
        super().__init__(direction, name, field_size)


class MemoryMappedInterface:
    """Memory mapped interface."""

    def __init__(self, reg_size=32, reg_offset=4):
        """Initialize."""
        self._registers = {}
        self._ports = {}
        self._parameters = {}
        self._reg_size = reg_size
        self._reg_addr_offset = reg_offset

    @property
    def registers(self):
        """Get registers."""
        return self._registers

    @property
    def reg_size(self):
        """Get register size."""
        return self._reg_size

    @property
    def parameters(self):
        """Get parameters."""
        return self._parameters

    @property
    def ports(self):
        """Get ports."""
        return self._ports

    def add_register(self, register):
        """Add a register to model."""
        if not isinstance(register, HDLRegister):
            raise TypeError("only HDLRegister allowed")

        if register.name in self._registers:
            raise KeyError(
                'register "{}" already' "exists".format(register.name)
            )

        self._registers[register.name] = register

    def get_register(self, name):
        """Get register objct by name."""
        if name not in self._registers:
            raise KeyError('register "{}" does not exist'.format(name))

        return self._registers[name]

    def add_port(self, port):
        """Add a port."""
        if not isinstance(port, FlagPort):
            raise TypeError("only FlagPort allowed")

        if port.name in self._ports:
            raise KeyError('port "{}" already' " exists".format(port.name))
        self._ports[port.name] = port

    def add_parameter(self, name, value):
        """Add a parameter."""
        if name in self._parameters:
            raise KeyError('parameter "{}" already exists'.format(name))

        self._parameters[name] = value

    def dumps(self):
        """Dump summary."""
        ret_str = "PARAMETERS:\n"
        for name, value in self._parameters.items():
            ret_str += "{} = {}\n".format(name.upper(), value.value.dumps())

        ret_str += "REGISTERS:\n"

        for regname, register in self._registers.items():
            ret_str += "0x{:02X}: {}\n".format(register.addr, regname)
            # dump field information
            for field in sorted(register.fields, key=lambda x: x.reg_slice[0]):
                ret_str += "{: <2}{} -> {} ({})\n".format(
                    field.permissions,
                    field.dumps_slice(),
                    field.name,
                    field.default_value,
                )

        ret_str += "PORTS:\n"
        for portname, port in self._ports.items():
            if port.direction == "out":
                dir_str = "<-"
            else:
                dir_str = "->"

            ret_str += "{} {} {}{}\n".format(
                port.name,
                dir_str,
                port.target_register.name,
                "." + port.target_field
                if port.target_field is not None
                else "",
            )

        return ret_str


def parse_mmap_str(text):
    """Parse mmap definition."""
    return MMAP_METAMODEL.model_from_str(text)


def parse_mmap_file(fpath):
    """Parse file."""
    with open(fpath, "r") as f:
        text = f.read()

    ret = parse_mmap_str(text)

    return (text, ret)
