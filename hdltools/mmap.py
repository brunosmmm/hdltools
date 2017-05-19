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

TEST_STR = """
#register_size 32;
//registers
register control;
register status;

//register fields
field control.IRQEN 0 RW description="Enable Interrupts";
field control.STOP_ON_ERROR 1 RW description="Stop on Error";
field status.IRQCLR 7 RW description="Interrupt flag; write 1 to clear";
field position=2..1 source=status.TEST access=R;
//field unknown.UNKNOWN 0;
//field position=2 source=status.Conflict access=R;

//outputs from register bits
output IRQ_EN source=control.IRQEN;
output STOP_ON_ERR source=control.STOP_ON_ERROR;
output UNKNOWN source=unknown.UNKNOWN;
"""


def bitfield_pos_to_slice(pos):
    """Convert to slice from parser object."""
    ret = [int(pos.left)]
    if pos.right is not None:
        ret.append(int(pos.right))

    return ret

if __name__ == "__main__":
    meta = metamodel_from_str(MMAP_COMPILER_GRAMMAR)
    decl = meta.model_from_str(TEST_STR)

    default_reg_size = 32
    declared_reg_size = None
    registers = {}
    for statement in decl.static_declarations:
        print(statement)
        if statement.__class__.__name__ == 'StaticStatement':
            if statement.var == 'register_size':
                print('Register size is {}'.format(statement.value))
                declared_reg_size = statement.value

    for statement in decl.statements:
        print(statement)
        if statement.__class__.__name__ == 'SlaveRegister':
            print('Creating register "{}"'.format(statement.name))
            if declared_reg_size is None:
                reg_size = default_reg_size
            else:
                reg_size = declared_reg_size
            registers[statement.name] = HDLRegister(statement.name,
                                                    size=declared_reg_size)

            # add properties
            for prop in statement.properties:
                registers[statement.name].add_property(**{prop.name:
                                                          prop.value})
        elif statement.__class__.__name__ == 'SlaveRegisterField':
            # parse
            source_reg = statement.source.register

            if source_reg not in registers:
                raise ValueError('unknown register: "{}"'.format(source_reg))

            formatted_slice = HDLRegisterField.dumps_slice(
                bitfield_pos_to_slice(statement.position))
            print('Adding field "{}" ({})'
                  ' to register slice "{}{}"'.format(statement.source.bit,
                                                     statement.access,
                                                     source_reg,
                                                     formatted_slice))

            reg_field = HDLRegisterField(statement.source.bit,
                                         bitfield_pos_to_slice(
                                             statement.position),
                                         statement.access)

            # add properties
            for prop in statement.properties:
                reg_field.add_properties(**{prop.name: prop.value})

            registers[source_reg].add_fields(reg_field)

    for name, reg in registers.items():
        print('{}: {}'.format(name, hex(reg.get_write_mask())))
