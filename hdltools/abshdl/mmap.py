"""Memory mapped interface description parser."""

from textx.metamodel import metamodel_from_str
from .registers import HDLRegister, HDLRegisterField
from .port import HDLModulePort
from .module import HDLModuleParameter
from .const import HDLIntegerConstant, HDLStringConstant
from .expr import HDLExpression

MMAP_COMPILER_GRAMMAR = """
AXIDescription:
  static_declarations*=StaticStatement params*=ParameterStatement statements*=Statement;
StaticStatement:
  '#' var=ID value=StaticValue ';';
ParameterStatement:
  'param' name=ID value=StaticValue ';';
Statement:
  (SlaveRegister | SlaveRegisterField | SlavePort) ';';
SlaveRegister:
  /register\s+/ name=TemplatedNameDecl ('at' address=RegisterAddress )?
  properties*=RegisterProperty;
TemplatedNameDecl[noskipws]:
  fragments += TemplatedNameDeclFragment;
TemplatedNameDeclFragment:
  fragment=/[a-zA-Z0-9_]*/ templates*=TemplatedNameDeclRule;
TemplatedNameDeclRule:
  '[' rule=/[^\]]+/ ']';
TemplatedNameSubst[noskipws]:
  fragments += TemplatedNameSubstFragment;
TemplatedNameSubstFragment:
  fragment=/[a-zA-Z0-9_]*/ templates*=TemplatedNameSubstFmt;
TemplatedNameSubstFmt:
  '{' arg=/[0-9]+/ '}';
SlaveRegisterField:
  'field' ('source='? source=FieldBitAccessor
           'position='? position=BitField
           'access='? access=AccessPermission
           ('default=' default=StaticValue)?
           properties*=RegisterProperty)#;
SlavePort:
  SlaveOutput | SlaveInput;
SlaveOutput:
  /output\s+/ descriptor=OutputDescriptor;
SlaveInput:
  /input\s+/  descriptor=InputDescriptor;
OutputDescriptor:
  name=TemplatedNameDecl source=SignalSource;
InputDescriptor:
  name=TemplatedNameDecl dest=SignalDestination;
SignalSource:
  'source' '=' field=SourceDestField;
SignalDestination:
  'dest' '=' field=SourceDestField;
SourceDestField:
  SourceBitAccessor | TemplatedNameSubst | ID;
SourceBitAccessor:
  register=TemplatedNameSubst '.' bit=ID;
FieldBitAccessor:
  register=ID '.' bit=ID;
RegisterProperty:
  name=ID '=' '"' value=/[^"]+/ '"';
StaticValue:
  id=ID | posint=PositiveInteger | hex=Hex;
RegisterAddress:
  Hex | PositiveInteger;
BitField:
  left=PositiveInteger ('..' right=PositiveInteger)?;
Hex:
  '0x' /[0-9a-fA-F]+/;
PositiveInteger:
  /[0-9]+/;
AccessPermission:
  'RW' | 'R' | 'W' ;
Comment:
  /\/\/.*$/;
"""


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


class MemoryMappedInterface(object):
    """Memory mapped interface."""

    def __init__(self):
        """Initialize."""
        self.registers = {}
        self.ports = {}
        self.parameters = {}
        self.current_reg_addr = 0
        self.set_reg_addr_offset(4)
        self.set_reg_size(32)

    def set_reg_size(self, size):
        """Set register size in bits."""
        self.reg_size = size

    def set_reg_addr_offset(self, off):
        """Set register address offset."""
        self.reg_addr_offset = off

    def next_available_address(self):
        """Find next available address."""
        if len(self.registers) == 0:
            self.current_reg_addr += self.reg_addr_offset
            return 0

        addr_set = set()
        for regname, register in self.registers.items():
            addr_set.add(register.addr)

        possible_offsets = range(
            0, max(addr_set) + self.reg_addr_offset, self.reg_addr_offset
        )
        for offset in possible_offsets:
            if offset in addr_set:
                continue
            else:
                self.current_reg_addr = offset
                return offset

        # must increment
        self.current_reg_addr = max(addr_set) + self.reg_addr_offset
        return self.current_reg_addr

    def parse_str(self, text):
        """Parse model from string."""
        meta = metamodel_from_str(MMAP_COMPILER_GRAMMAR)
        decl = meta.model_from_str(text)

        declared_reg_size = None
        for statement in decl.static_declarations:
            if statement.__class__.__name__ == "StaticStatement":
                if statement.var == "register_size":
                    if statement.value.posint is not None:
                        self.set_reg_size(int(statement.value.posint))
                    elif statement.value.hex is not None:
                        self.set_reg_size(
                            int(statement.value.hex.strip("0x"), 16)
                        )
                    elif statement.value.id is not None:
                        raise ValueError(
                            "Identifier or expressions not" " supported"
                        )
                elif statement.var == "addr_mode":
                    if statement.value.id == "byte":
                        self.set_reg_addr_offset(int(self.reg_size / 8))
                    elif statement.value.id == "word":
                        self.set_reg_addr_offset(1)
                    elif statement.value.id is not None:
                        raise ValueError(
                            'addr_mode can only be "byte" or' '"word"'
                        )

        for statement in decl.params:
            if statement.__class__.__name__ == "ParameterStatement":
                if statement.value.hex is not None:
                    val = int(statement.value.hex.strip("0x"), 16)
                    radix = "h"
                elif statement.value.posint is not None:
                    val = int(statement.value.posint)
                    radix = "d"
                elif statement.value.id is not None:
                    raise ValueError("Identifier or expressions not supported")

                hdl_val = HDLIntegerConstant(val, radix=radix)
                param = HDLModuleParameter(statement.name, "integer", hdl_val)
                self.add_parameter(statement.name, param)

        for statement in decl.statements:
            if statement.__class__.__name__ == "SlaveRegister":

                if statement.address is not None:
                    reg_addr = int(statement.address)
                else:
                    reg_addr = self.next_available_address()

                if len(statement.name.fragments) > 1:
                    raise NotImplementedError("not implemented")

                # detect generator patterns
                if len(statement.name.fragments) == 1:
                    if not statement.name.fragments[0].templates:
                        # simple declaration
                        register = HDLRegister(statement.name.fragments[0].fragment,
                                               size=self.reg_size, addr=reg_addr)
                        # add properties
                        for prop in statement.properties:
                            register.add_properties(**{prop.name: prop.value})

                        self.add_register(register)
                    else:
                        if len(statement.name.fragments[0].templates) > 1:
                            raise NotImplementedError("not implemented")

                        template_str = statement.name.fragments[0].templates[0].rule
                        try:
                            start, end = template_str.split("-")
                            addr = reg_addr
                            for reg in range(int(start), int(end)+1):
                                reg_name = statement.name.fragments[0].fragment + str(reg)
                                register = HDLRegister(reg_name, size=self.reg_size, addr=addr)

                                for prop in statement.properties:
                                    register.add_properties(**{prop.name: prop.value.format(str(reg))})

                                self.add_register(register)
                                addr = self.next_available_address()
                        except:
                            raise RuntimeError("error in template rule")

            elif statement.__class__.__name__ == "SlaveRegisterField":
                # parse
                source_reg = statement.source.register

                if source_reg not in self.get_register_list():
                    raise ValueError(
                        "unknown register:" ' "{}"'.format(source_reg)
                    )

                slicesize = slice_size(
                    bitfield_pos_to_slice(statement.position)
                )
                if statement.default is not None:
                    if statement.default.posint is not None:
                        defval = int(statement.default.posint)
                        param_min_size = HDLIntegerConstant.minimum_value_size(
                            defval
                        )
                    elif statement.default.hex is not None:
                        defval = int(statement.default.hex.strip("0x"), 16)
                        param_min_size = HDLIntegerConstant.minimum_value_size(
                            defval
                        )
                    elif statement.default.id is not None:
                        # search into parameters
                        val = statement.default.id.strip()
                        if val in self.parameters:
                            # defval = self.parameters[val].value.value
                            # param_min_size = self.parameters[val].value.size
                            param_min_size = 0
                            defval = HDLExpression(val, size=slicesize)
                        else:
                            raise ValueError(
                                "Unknown" ' identifier: "{}":'.format(val)
                            )
                    # check if it fits
                    if slicesize < param_min_size:
                        raise ValueError(
                            'value "{}" does not fit'
                            ' field "{}"'.format(defval, statement.source.bit)
                        )
                else:
                    defval = 0

                reg_field = HDLRegisterField(
                    statement.source.bit,
                    bitfield_pos_to_slice(statement.position),
                    statement.access,
                    default_value=defval,
                )

                # add properties
                for prop in statement.properties:
                    reg_field.add_properties(**{prop.name: prop.value})

                self.registers[source_reg].add_fields(reg_field)
            # TODO parse ports
            elif statement.__class__.__name__ == "SlaveOutput":
                descriptor = statement.descriptor
                name = descriptor.name
                source = descriptor.source.field
                if isinstance(source, str):
                    src_reg = source
                    src_bit = None
                elif source.__class__.__name__ == "SourceBitAccessor":
                    if len(source.register.fragments) > 1:
                        raise NotImplementedError
                    if len(source.register.fragments[0].templates) > 1:
                        raise NotImplementedError
                    src_reg = source.register
                    src_bit = source.bit
                else:
                    # just a templated name
                    if len(source.fragments) > 1:
                        raise NotImplementedError
                    if len(source.fragments[0].templates) > 1:
                        raise NotImplementedError
                    src_reg = source
                    src_bit = None

                if len(name.fragments) > 1:
                    raise NotImplementedError
                if len(name.fragments[0].templates) > 1:
                    raise NotImplementedError
                elif not name.fragments[0].templates:
                    # simple declaration
                    if src_reg.fragments[0].templates:
                        raise RuntimeError("no value to substitute in register templated name")
                    src_reg = src_reg.fragments[0].fragment
                    if src_reg not in self.registers:
                        raise KeyError('invalid register: "{}"'.format(src_reg))

                    src_reg = self.registers[src_reg]
                    if src_bit is not None and src_reg.has_field(src_bit) is False:
                        raise KeyError('invalid field: "{}"'.format(src_bit))
                    port = FlagPort(src_reg, src_bit, "out", name.fragments[0].fragment)
                    self.add_port(port)
                else:
                    try:
                        start, end = name.fragments[0].templates[0].rule.split("-")
                    except:
                        raise RuntimeError("error in fragment rule")
                    for port in range(int(start), int(end)+1):
                        _reg = (src_reg.fragments[0].fragment +
                                src_reg.fragments[0].templates[0].arg.format(port))
                        if _reg not in self.registers:
                            raise KeyError('invalid register: "{}"'.format(_reg))

                        _reg = self.registers[_reg]
                        if src_bit is not None and _reg.has_field(src_bit) is False:
                            raise KeyError('invalid field: "{}"'.format(src_bit))

                        port = FlagPort(_reg, src_bit, "out", name.fragments[0].fragment + str(port))
                        self.add_port(port)
            elif statement.__class__.__name__ == "SlaveInput":
                descriptor = statement.descriptor
                name = descriptor.name
                dest = descriptor.dest.field
                if isinstance(dest, str):
                    dest_reg = dest
                    dest_bit = None
                elif dest.__class__.__name__ == "SourceBitAccessor":
                    if len(dest.register.fragments) > 1:
                        raise NotImplementedError
                    if len(dest.register.fragments[0].templates) > 1:
                        raise NotImplementedError
                    dest_reg = dest.register
                    dest_bit = dest.bit
                else:
                    # just a templated name
                    if len(dest.fragments) > 1:
                        raise NotImplementedError
                    if len(dest.fragments[0].templates) > 1:
                        raise NotImplementedError
                    dest_reg = source
                    dest_bit = None


                if len(name.fragments) > 1:
                    raise NotImplementedError
                if len(name.fragments[0].templates) > 1:
                    raise NotImplementedError
                elif not name.fragments[0].templates:
                    # simple declaration
                    if dest_reg.fragments[0].templates:
                        raise RuntimeError("no value to substitute in register templated name")
                    dest_reg = dest_reg.fragments[0].fragment
                    if dest_reg not in self.registers:
                        raise KeyError('invalid register: "{}"'.format(dest_reg))

                    dest_reg = self.registers[dest_reg]
                    if dest_bit is not None and dest_reg.has_field(dest_bit) is False:
                        raise KeyError('invalid field: "{}"'.format(dest_bit))
                    port = FlagPort(dest_reg, dest_bit, "in", name.fragments[0].fragment)
                    self.add_port(port)
                else:
                    try:
                        start, end = name.fragments[0].templates[0].split("-")
                    except:
                        raise RuntimeError("error in fragment rule")
                    for port in range(int(start), int(end)+1):
                        _reg = (dest_reg.fragments[0].fragment +
                                    dest_reg.fragments[0].templates[0].format(port))
                        if _reg not in self.registers:
                            raise KeyError('invalid register: "{}"'.format(_reg))

                        _reg = self.registers[_reg]
                        if dest_bit is not None and _reg.has_field(dest_bit) is False:
                            raise KeyError('invalid field: "{}"'.format(dest_bit))

                        port = FlagPort(_reg, dest_bit, "in", name.fragments[0].fragment + str(port))
                        self.add_port(port)

    def parse_file(self, filename):
        """Parse model from file."""
        with open(filename, "r") as f:
            self.parse_str(f.read())

    def add_register(self, register):
        """Add a register to model."""
        if not isinstance(register, HDLRegister):
            raise TypeError("only HDLRegister allowed")

        if register.name in self.registers:
            raise KeyError(
                'register "{}" already' "exists".format(register.name)
            )

        self.registers[register.name] = register

    def get_register_list(self):
        """Get register name list."""
        return list(self.registers.keys())

    def get_register(self, name):
        """Get register objct by name."""
        if name not in self.registers:
            raise KeyError('register "{}" does not exist'.format(name))

        return self.registers[name]

    def add_port(self, port):
        """Add a port."""
        if not isinstance(port, FlagPort):
            raise TypeError("only FlagPort allowed")

        if port.name in self.ports:
            raise KeyError('port "{}" already' " exists".format(port.name))
        self.ports[port.name] = port

    def add_parameter(self, name, value):
        """Add a parameter."""
        if name in self.parameters:
            raise KeyError('parameter "{}" already exists'.format(name))

        self.parameters[name] = value

    def dumps(self):
        """Dump summary."""
        ret_str = "PARAMETERS:\n"
        for name, value in self.parameters.items():
            ret_str += "{} = {}\n".format(name.upper(), value.value.dumps())

        ret_str += "REGISTERS:\n"

        for regname, register in self.registers.items():
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
        for portname, port in self.ports.items():
            if port.direction == "out":
                dir_str = "<-"
            else:
                dir_str = "->"

            ret_str += "{} {} {}{}\n".format(
                port.name, dir_str, port.target_register.name,
                "." + port.target_field if port.target_field is not None else ""
            )

        return ret_str
