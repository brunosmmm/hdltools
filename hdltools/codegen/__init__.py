"""Code generation primitives."""

import hdltools.verilog.codegen
import hdltools.vhdl.codegen

BUILTIN_CODE_GENERATORS = {
    "verilog": hdltools.verilog.codegen.VerilogCodeGenerator,
    "vhdl": hdltools.vhdl.codegen.VHDLCodeGenerator,
}
