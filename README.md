# HDL TOOLS

A comprehensive Python library for RTL (Register Transfer Level) hardware design manipulation, providing utilities for HDL abstraction, code generation, simulation, and analysis. The library bridges the gap between high-level Python programming and low-level hardware description languages.

## Core Features

### HDL Code Generation (Production Ready)
* **HDL Intermediate Representation** (hdltools.abshdl.*) - Language-agnostic hardware representation
* **Verilog Code Generator** (hdltools.verilog.codegen) - Complete Verilog output from IR
* **VHDL Code Generator** (hdltools.vhdl.codegen) - Complete VHDL output from IR with functional equivalence validation
* **Dual-Language Support** - Generate both Verilog and VHDL from the same source
* **Python HDL Syntax** (hdltools.abshdl.highlvl) - Write HDL using pure Python syntax with decorators

### Memory Map & AXI Tools (Production Ready)
* **Memory Map Parser** (hdltools.abshdl.mmap) - TextX-based memory map description language
* **AXI Slave Builder** (tools/axi_slave_builder.py) - Generate AXI memory-mapped slaves
* **Documentation Generator** (tools/mmap_docgen.py) - Automatic markdown docs from memory maps

### VCD Analysis Framework (Production Ready)
* **VCD Parser/Generator** (hdltools.vcd) - Complete VCD file parsing and generation
* **Cross-Language VCD Comparison** (hdltools.vcd.compare) - Compare Verilog vs VHDL simulation outputs
* **Hierarchy Analysis** (hdltools.vcd) - VCD scope analysis and signal tracking
* **Pattern Matching** (hdltools.vcd, hdltools.pattern) - Temporal value pattern detection
* **Event Tracking** - Dynamic event monitoring with callbacks and statistics

### Simulation & Testing (Production Ready)
* **Hybrid Simulation** (hdltools.sim.*) - Objects can be both simulated and compiled to HDL
* **HDL Compiler** (hdltools.sim.hdl) - AST-based Python-to-HDL conversion
* **Functional Equivalence Testing** - Automated validation that Verilog and VHDL produce identical results

### Additional Tools (Various Maturity Levels)
* **Verilog Parser** (hdltools.verilog.parser) - Module declaration parsing
* **Vector Generator** (hdltools.vecgen, tools/vgc) - DSL/compiler for testbench input generation
* **HDL Patterns** (hdltools.hdllib.patterns) - Common HDL design patterns
* **AXI Memory-Mapped Models** (hdltools.hdllib.aximm) - AXI slave models using IR
* **LaTeX Documentation** (hdltools.latex.*) - Module block diagram generation

## Command-Line Tools

The library includes 8 command-line tools for various HDL and verification tasks:

1. **`axi_slave_builder`** - Generate AXI memory-mapped slaves from specifications
2. **`mmap_docgen`** - Create documentation from memory map descriptions  
3. **`vgc`** - Vector generation compiler for test input creation
4. **`vcdtracker`** - Value pattern tracking in VCD files
5. **`vcdhier`** - VCD hierarchy exploration and analysis
6. **`vcdevts`** - Event counting and analysis from VCD files
7. **`inputgen`** - Test vector generation from JSON configurations
8. **`fnboundary`** - Function boundary detection from assembly dumps

## Status & Quality

* **Test Coverage**: 79/79 tests passing (100% pass rate)
* **Python Support**: 3.10+ with modern dependency management
* **Dependencies**: Updated to latest versions (textX 4.2.2, removed deprecated pkg_resources)
* **Validation**: Comprehensive functional equivalence testing between generated Verilog and VHDL
* **Production Use**: Core HDL generation and VCD analysis components are stable and validated
