"""Verilog module declaration parser."""

from textx.metamodel import metamodel_from_str


VERILOG_DECL_GRAMMAR = """
VerilogFile:
  modDecl=ModuleDeclaration /.*/*;
ModuleDeclaration:
  'module' modName=ID '('ports*=ModulePort fport=FinalModulePort')' ';';
ModulePort:
  FinalModulePort ',';
FinalModulePort:
  (ModuleInput|ModuleOutput);
ModuleInput:
  'input' decl=ModulePortDeclaration;
ModuleOutput:
  'output' decl=ModulePortDeclaration;
ModulePortDeclaration:
  ('wire'|'reg')? (range=VectorRange)? portName=ID;
VectorRange:
  '[' leftSize=VectorRangeElement ':' rightSize=VectorRangeElement ']';
VectorRangeElement:
  SimpleExpression;
SimpleExpression:
  Value (('+'|'-'|'*'|'/') Value)*;
Value:
  ID | INT | (SimpleExpression);
"""


class VerilogModuleParser(object):
    """Parse module declarations in verilog files."""

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

        for port in module_decl.modDecl.ports:
            print(port)
