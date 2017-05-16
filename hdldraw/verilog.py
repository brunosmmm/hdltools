"""Verilog module declaration parser."""

from textx.metamodel import metamodel_from_str
from .hdl import HDLModulePort, HDLModule, HDLModuleParameter, HDLExpression
import re
import ast

VERILOG_DECL_GRAMMAR = """
VerilogFile:
  VerilogTimescale? mod_decl=ModuleDeclaration /.*/*;
VerilogTimescale:
  '`' 'timescale' val_1=/[0-9]+/ /[unpm]s/ '/' val_2=/[0-9]+/ /[unpm]s/;
ModuleDeclaration:
  'module' mod_name=ID param_decl=ModuleParameterDecl?
  '('ports*=ModulePort fport=FinalModulePort')' ';';
ModuleParameterDecl:
  '#(' params*=ModuleParameter fparam=FinalParameter ')';
ModuleParameter:
  FinalParameter ',';
FinalParameter:
  'parameter' par_type=ParameterType? par_name=ID ('=' def_val=ParameterValue)?;
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
  /[0-9a-zA-Z_\+\-\*\/\(\))\$]+/;
ParameterValue:
  INT | BitString;
ParameterType:
  'integer';
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


def verilog_bitstring_to_int(bitstring):
    """Parse bitstring and return value."""
    HEX_BITSTRING_REGEX = re.compile(r'([0-9]+)?\'h([0-9a-fA-F]+)')
    DEC_BITSTRING_REGEX = re.compile(r'([0-9]+)?\'d([0-9]+)')
    BIN_BITSTRING_REGEX = re.compile(r'([0-9]+)?\'b([01]+)')

    m_hex = HEX_BITSTRING_REGEX.match(bitstring)
    m_dec = DEC_BITSTRING_REGEX.match(bitstring)
    m_bin = BIN_BITSTRING_REGEX.match(bitstring)

    if m_hex is not None:
        if m_hex.group == '':
            width = None
        else:
            width = int(m_hex.group(1))
        return (width, int(m_hex.group(2), 16))
    elif m_dec is not None:
        if m_dec.group == '':
            width = None
        else:
            width = int(m_dec.group(1))
        return (width, int(m_dec.group(2), 10))
    elif m_bin is not None:
        if m_bin.group == '':
            width = None
        else:
            width = int(m_bin.group(1))
        return (width, int(m_bin.group(2), 2))
    else:
        raise ValueError('could not convert bitstring')


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

        # create and add parameters
        if module_decl.mod_decl.param_decl is not None:
            params = module_decl.mod_decl.param_decl.params[:]
            params.append(module_decl.mod_decl.param_decl.fparam)
            for param in params:
                hdl_param = HDLModuleParameter(param_name=param.par_name,
                                               param_type=param.par_type,
                                               param_default=param.def_val)

                hdl_mod.add_parameters(hdl_param)

        self.hdl_model = hdl_mod

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

                # use ast to parse, avoiding complicated grammar
                left_str = port.decl.srange.left_size.replace('$', '_')
                right_str = port.decl.srange.right_size.replace('$',
                                                                '_')
                left_tree = ast.parse(left_str,
                                      mode='eval')
                right_tree = ast.parse(right_str,
                                       mode='eval')
                left_deps = self._find_dependencies(left_tree)
                right_deps = self._find_dependencies(right_tree)

                # search dependencies in parameters
                for dep in left_deps:
                    if dep not in self.hdl_model.get_param_names():
                        raise KeyError('unknown identifier: {}'.format(dep))
                for dep in right_deps:
                    if dep not in self.hdl_model.get_param_names():
                        raise KeyError('unknown identifier: {}'.format(dep))

                size = (HDLExpression(left_tree), HDLExpression(right_tree))
            else:
                size = (0, 0)
            try:
                hdl_port = HDLModulePort(direction=direction,
                                         name=name,
                                         size=size)
            except TypeError:
                pass

            self.hdl_model.add_ports(hdl_port)

    def _find_dependencies(self, node):
        if isinstance(node, ast.Expression):
            return self._find_dependencies(node.body)
        elif isinstance(node, ast.BinOp):
            left_node_dep = self._find_dependencies(node.left)
            right_node_dep = self._find_dependencies(node.right)
            deps = []
            deps.extend(left_node_dep)
            deps.extend(right_node_dep)
            return deps
        elif isinstance(node, (ast.Num, ast.Call)):
            return []
        elif isinstance(node, ast.Name):
            return [node.id]

    def get_module(self):
        """Get intermediate module representation."""
        return self.hdl_model
