"""Verilog module declaration parser."""

from textx.metamodel import metamodel_from_str


VERILOG_DECL_GRAMMAR = """
VerilogFile:
  mod_decl=ModuleDeclaration /.*/*;
ModuleDeclaration:
  'module' mod_name=ID '('ports*=ModulePort fport=FinalModulePort')' ';';
ModulePort:
  FinalModulePort ',';
FinalModulePort:
  (ModuleInput|ModuleOutput|ModuleInout);
ModuleInout:
  'inout' decl=ModulePortDeclaration;
ModuleInput:
  'input' decl=ModulePortDeclaration;
ModuleOutput:
  'output' decl=ModulePortDeclaration;
ModulePortDeclaration:
  ('wire'|'reg')? (srange=VectorRange)? port_name=ID;
VectorRange:
  '[' left_size=VectorRangeElement ':' right_size=VectorRangeElement ']';
VectorRangeElement:
  SimpleExpression;
SimpleExpression:
  Value (('+'|'-'|'*'|'/') Value)*;
Value:
  ID | INT | (SimpleExpression);
"""


from .hdl import HDLModulePort, HDLVectorDescriptor, HDLModule


class VerilogModuleParser(object):
    """Parse module declarations in verilog files."""

    _class_to_port_dir = {'ModuleInput': 'in',
                          'ModuleOutput': 'out',
                          'ModuleInout': 'inout'}

    def __init__(self, module_file):
        """Initialize.

        Args
        ----
        module_file: str
           Path to file being parsed
        """
        self.mod_file = module_file

        self._parse_file()

    def _parse_file(self):
        """Parse file."""
        meta_model = metamodel_from_str(VERILOG_DECL_GRAMMAR)

        module_decl = meta_model.model_from_file(self.mod_file)

        # create module object
        hdl_mod = HDLModule(module_decl.mod_decl.mod_name)

        # create and add ports
        for port in module_decl.mod_decl.ports:
            # ugly, but not my fault
            direction = self._class_to_port_dir[port.__class__.__name__]
            name = port.decl.port_name
            if port.decl.srange is not None:
                size = (port.decl.srange.left_size,
                        port.decl.srange.right_size)
            else:
                size = 1
            hdl_port = HDLModulePort(direction=direction,
                                     name=name,
                                     size=size)

            hdl_mod.add_ports(hdl_port)
