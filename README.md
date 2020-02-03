# HDL TOOLS

A few tools to enable code generation automation and other useful tasks.

Includes (everything is a WIP):

* Simple HDL Intermediate representation abstractions (hdltools.abshdl.*)
* Verilog module declaration parser (hdltools.verilog.parser)
* Verilog code generator (generates from intermediate representation) (hdltools.verilog.codegen)
* Memory mapped interface description language parser (hdltools.abshdl.mmap)
* AXI Slave builder from memory mapped interface description (tools/axi_slave_builder.py)
* Doc (markdown) builder from memory mapped interface description (tools/mmap_docgen.py)
* Module block drawing output with LaTeX (hdltools.latex.*)
* Generate HDL representation / code usign pure python syntax (hdltools.abshdl.highlvl)
* Generate exhaustively used HDL patterns easily (hdltools.hdllib.patterns)
* AXI Memory-mapped slave model using Intermediate Representation (hdltools.hdllib.aximm)
* Simple simulation framework (hdltools.sim.*)
* Simulation model HDL Compiler (hdltools.sim.hdl)
* Vector generator DSL/compiler for testbench input (hdltools.vecgen, tools/vgc)
* VCD parser / generator / intermediate representation (hdltools.vcd)
* VCD Hierarchy analysis, temporal value pattern tracking (hdltools.vcd)
* Sequential pattern matching (hdltools.pattern)
