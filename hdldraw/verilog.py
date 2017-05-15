"""Verilog module declaration parser."""

from textx.metamodel import metamodel_from_str
from .hdl import HDLModulePort, HDLModule, HDLModuleParameter

VERILOG_DECL_GRAMMAR = """
VerilogFile:
  mod_decl=ModuleDeclaration /.*/*;
ModuleDeclaration:
  'module' mod_name=ID param_decl=ModuleParameterDecl?
  '('ports*=ModulePort fport=FinalModulePort')' ';';
ModuleParameterDecl:
  '#(' params*=ModuleParameter fparam=FinalParameter ')';
ModuleParameter:
  FinalParameter ',';
FinalParameter:
  'parameter' par_type=ID? par_name=ID ('=' def_val=ParameterValue)?;
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
  Expression;
Expression:
  Sum;
Sum:
  Product (('+'|'-') Product)*;
Product:
  Value ('*' Value)*;
Value:
  ID | INT | ('(' Expression ')');
ParameterValue:
  INT | BitString;
BitString:
  BinBitString | DecBitString | HexBitString;
BinBitString:
  width=INT? "'b" val=/(0|1)+/;
DecBitString:
  width=INT? "'d" val=/[0-9]+/;
HexBitString:
  width=INT? "'h" val=/[0-9a-fA-F]+/;
Comment:
  /\/\/.*$/;
"""


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
        ports = module_decl.mod_decl.ports[:]
        # add last port
        ports.append(module_decl.mod_decl.fport)
        for port in ports:
            # ugly, but not my fault
            direction = self._class_to_port_dir[port.__class__.__name__]
            name = port.decl.port_name
            if port.decl.srange is not None:
                size = (port.decl.srange.left_size,
                        port.decl.srange.right_size)
            else:
                size = 1
            try:
                hdl_port = HDLModulePort(direction=direction,
                                         name=name,
                                         size=size)
            except TypeError:
                continue  # just for testing

            hdl_mod.add_ports(hdl_port)

        # same, for parameters
        if module_decl.mod_decl.param_decl is not None:
            params = module_decl.mod_decl.param_decl.params[:]
            params.append(module_decl.mod_decl.param_decl.fparam)
            for param in params:
                hdl_param = HDLModuleParameter(param_name=param.par_name,
                                               param_type=param.par_type,
                                               param_default=param.def_val)

                hdl_mod.add_parameters(hdl_param)

        self.hdl_model = hdl_mod

    def get_module(self):
        """Get intermediate module representation."""
        return self.hdl_model
