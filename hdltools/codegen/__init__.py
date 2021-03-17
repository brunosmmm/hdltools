"""Code generation primitives."""

import hdltools.verilog.codegen
import hdltools.specc.codegen

BUILTIN_CODE_GENERATORS = {
    "verilog": hdltools.verilog.codegen.VerilogCodeGenerator,
    "specc": hdltools.specc.codegen.SpecCCodeGenerator,
}
