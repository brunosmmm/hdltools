"""Test tools."""
import pytest
import os
from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.template import HDLTemplateParser
from hdltools.mmap import parse_mmap_str
from hdltools.mmap.builder import MMBuilder


def test_vec():
    """Test verilog code generator."""
    print(VerilogCodeGenerator.dumps_vector(1, 32, "h"))
    print(VerilogCodeGenerator.dumps_vector(1, 32, "d"))
    print(VerilogCodeGenerator.dumps_vector(1, 32, "b"))

    with pytest.raises(ValueError):
        _ = VerilogCodeGenerator.dumps_vector(256, 8, "b")

    with pytest.raises(ValueError):
        _ = VerilogCodeGenerator.dumps_vector(256, 8, "x")


def test_define():
    """Test define."""
    print(VerilogCodeGenerator.dumps_define("NAME", "VALUE"))


def test_template():
    """Test template."""
    template_file = os.path.join("assets", "verilog", "axi_slave.v")
    parser = HDLTemplateParser()
    parser.parse_file(template_file)
    parser.insert_contents(
        list(parser.locations.keys())[0], "line1\nline2\nline3"
    )

    with pytest.raises(ValueError):
        parser.dump_templated("test.v")


def test_mmap():
    """Test memory-mapped AXI slave generator."""
    TEST_STR = """
    define register_size 32
    define addr_mode byte
    //registers
    register control {
      field IRQEN position=0 access=RW { property description="Enable Interrupts" }
      field STOP_ON_ERROR position=1 access=RW { property  description="Stop on Error" }
    }
    register status {
      field IRQCLR position=7 access=RW { property description="Interrupt flag; write 1 to clear" }
      field TEST position=2..1 access=R
    }

    //outputs from register bits
    output IRQ_EN source=control.IRQEN
    output STOP_ON_ERR source=control.STOP_ON_ERROR
    """

    decl = parse_mmap_str(TEST_STR)
    mmap = MMBuilder(TEST_STR)
    mmap.visit(decl)
