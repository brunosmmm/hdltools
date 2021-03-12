"""Test verilog module parser."""

from hdltools.verilog.parser import VerilogModuleParser


def test_vparser():

    VerilogModuleParser("tests/assets/test.v")
