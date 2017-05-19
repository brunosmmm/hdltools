"""Memory mapped interface description parser."""

from textx.metamodel import metamodel_from_str
from .registers import HDLRegister, HDLRegisterField

MMAP_COMPILER_GRAMMAR = """
AXIDescription:
  static_declarations*=StaticStatement statements*=Statement;
StaticStatement:
  '#' var=ID value=PositiveInteger ';';
Statement:
  (SlaveRegister | SlaveRegisterField | SlavePort) ';';
SlaveRegister:
  'register'  name=ID properties*=RegisterProperty;
SlaveRegisterField:
  'field' ('source='? source=BitAccessor
           'position='? position=BitField
           'access='? access=AccessPermission
           properties*=RegisterProperty)#;
SlavePort:
  SlaveOutput | SlaveInput;
SlaveOutput:
  'output' descriptor=PortDescriptor;
SlaveInput:
  'input'  descriptor=PortDescriptor;
PortDescriptor:
  name=ID source=SignalSource;
SignalSource:
  'source' '=' BitAccessor;
BitAccessor:
  register=ID '.' bit=ID;
RegisterProperty:
  name=ID '=' '"' value=/[^"]+/ '"';
BitField:
  left=PositiveInteger ('..' right=PositiveInteger)?;
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


class MemoryMappedInterface(object):
    """Memory mapped interface."""

    def __init__(self):
        """Initialize."""
        self.registers = {}

    def parse_str(self, text):
        """Parse model from string."""
        meta = metamodel_from_str(MMAP_COMPILER_GRAMMAR)
        decl = meta.model_from_str(text)

        default_reg_size = 32
        declared_reg_size = None
        for statement in decl.static_declarations:
            if statement.__class__.__name__ == 'StaticStatement':
                if statement.var == 'register_size':
                    declared_reg_size = statement.value

        for statement in decl.statements:
            if statement.__class__.__name__ == 'SlaveRegister':
                if declared_reg_size is None:
                    reg_size = default_reg_size
                else:
                    reg_size = declared_reg_size
                register = HDLRegister(statement.name,
                                       size=declared_reg_size)

                # add properties
                for prop in statement.properties:
                    register.add_property(**{prop.name:
                                             prop.value})

                self.add_register(register)
            elif statement.__class__.__name__ == 'SlaveRegisterField':
                # parse
                source_reg = statement.source.register

                if source_reg not in self.get_register_list():
                    raise ValueError('unknown register:'
                                     ' "{}"'.format(source_reg))

                reg_field = HDLRegisterField(statement.source.bit,
                                             bitfield_pos_to_slice(
                                                 statement.position),
                                             statement.access)

                # add properties
                for prop in statement.properties:
                    reg_field.add_properties(**{prop.name: prop.value})

                self.registers[source_reg].add_fields(reg_field)
            # TODO parse ports

    def parse_file(self, filename):
        """Parse model from file."""
        with open(filename, 'r') as f:
            self.parse_str(f.read())

    def add_register(self, register):
        """Add a register to model."""
        if not isinstance(register, HDLRegister):
            raise TypeError('only HDLRegister allowed')

        if register.name in self.registers:
            raise KeyError('register "{}" already'
                           'exists'.format(register.name))

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
        pass
