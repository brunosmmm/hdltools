"""Memory-mapped interface."""

from hdltools.abshdl import HDLObject
from hdltools.abshdl.registers import HDLRegister
from hdltools.mmap import FlagPort


class MemoryMappedInterface(HDLObject):
    """Memory mapped interface."""

    def __init__(self, reg_size=32, reg_offset=4):
        """Initialize."""
        super().__init__()
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

    @staticmethod
    def _dump_properties(properties):
        """Dump properties."""
        has_properties = False
        props = []
        for pname, pval in properties.items():
            if pname == "description":
                continue
            else:
                has_properties = True
            if isinstance(pval, bool):
                props.append(pname)
            else:
                props.append(f"{pname}={pval}")

        if has_properties is False:
            return ""

        return "[" + ", ".join(props) + "]"

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
                ret_str += "{: <2}{} -> {} ({}) {}\n".format(
                    field.permissions,
                    field.dumps_slice(),
                    field.name,
                    field.default_value,
                    self._dump_properties(field.properties),
                )

        ret_str += "PORTS:\n"
        for portname, port in self._ports.items():
            if port.direction == "out":
                dir_str = "<-"
            else:
                dir_str = "->"

            ret_str += "{} {} {}{}{}\n".format(
                port.name,
                dir_str,
                port.target_register.name,
                "." + port.target_field
                if port.target_field is not None
                else "",
                " [trigger]" if port.is_trigger else "",
            )

        return ret_str
