"""Test VHDL library header generation."""

import pytest
from hdltools.vhdl.codegen import VHDLCodeGenerator
from hdltools.abshdl.module import HDLModule, input_port, output_port
from hdltools.abshdl.signal import HDLSignal
from hdltools.abshdl.assign import HDLAssignment


class TestVHDLLibraryHeaders:
    """Test VHDL automatic library header generation."""

    def test_library_detection_basic(self):
        """Test basic library detection for std_logic types."""
        vhdl_gen = VHDLCodeGenerator()
        
        # Create simple module with std_logic ports
        @HDLModule("test_basic", ports=[
            input_port("clk"),
            input_port("rst"),
            output_port("data", size=8)
        ])
        def basic_module(mod):
            pass
        
        module = basic_module()
        
        # Test library detection
        libraries = vhdl_gen._analyze_required_libraries(module)
        assert 'std_logic_1164' in libraries
        
        # Test header generation
        headers = vhdl_gen._generate_library_headers(libraries)
        assert 'library ieee;' in headers
        assert 'use ieee.std_logic_1164.all;' in headers

    def test_library_detection_numeric(self):
        """Test library detection for numeric operations."""
        vhdl_gen = VHDLCodeGenerator()
        
        # Test different library combinations
        test_cases = [
            ({'std_logic_1164'}, "Basic digital types"),
            ({'std_logic_1164', 'numeric_std'}, "Digital + numeric"),
            ({'std_logic_1164', 'numeric_std', 'math_real'}, "All IEEE libraries"),
            (set(), "No libraries")
        ]
        
        for libraries, description in test_cases:
            headers = vhdl_gen._generate_library_headers(libraries)
            
            if 'std_logic_1164' in libraries:
                assert 'library ieee;' in headers
                assert 'use ieee.std_logic_1164.all;' in headers
            
            if 'numeric_std' in libraries:
                assert 'use ieee.numeric_std.all;' in headers
            
            if 'math_real' in libraries:
                assert 'use ieee.math_real.all;' in headers
            
            if not libraries:
                assert headers == ""

    def test_module_with_library_headers(self):
        """Test complete module generation with library headers."""
        @HDLModule("test_with_headers", ports=[
            input_port("clk"),
            input_port("data_in", size=8),
            output_port("data_out", size=8)
        ])
        def test_module(mod):
            # Add a signal to ensure std_logic_1164 is detected
            temp_signal = HDLSignal("comb", "temp", size=8)
            mod.add(temp_signal)
            
            # Add assignment
            assign = HDLAssignment(mod.ports[2].signal, temp_signal)
            mod.add(assign)
        
        module = test_module()
        vhdl_gen = VHDLCodeGenerator()
        vhdl_code = vhdl_gen.dump_element(module)
        
        # Verify library headers are included
        assert 'library ieee;' in vhdl_code
        assert 'use ieee.std_logic_1164.all;' in vhdl_code
        
        # Verify entity comes after headers
        lines = vhdl_code.split('\n')
        library_line = next(i for i, line in enumerate(lines) if 'library ieee;' in line)
        entity_line = next(i for i, line in enumerate(lines) if 'entity test_with_headers' in line)
        assert library_line < entity_line

    def test_library_header_ordering(self):
        """Test that library headers are properly ordered."""
        vhdl_gen = VHDLCodeGenerator()
        
        libraries = {'std_logic_1164', 'numeric_std', 'math_real'}
        headers = vhdl_gen._generate_library_headers(libraries)
        
        lines = headers.split('\n')
        library_lines = [line for line in lines if line.strip()]
        
        # Should start with library declaration
        assert library_lines[0] == 'library ieee;'
        
        # std_logic_1164 should come before numeric_std
        std_logic_idx = next(i for i, line in enumerate(library_lines) 
                           if 'std_logic_1164' in line)
        numeric_idx = next(i for i, line in enumerate(library_lines) 
                          if 'numeric_std' in line)
        assert std_logic_idx < numeric_idx

    def test_empty_library_set(self):
        """Test behavior with empty library set."""
        vhdl_gen = VHDLCodeGenerator()
        headers = vhdl_gen._generate_library_headers(set())
        assert headers == ""

    def test_textio_library(self):
        """Test textio library generation."""
        vhdl_gen = VHDLCodeGenerator()
        libraries = {'textio'}
        headers = vhdl_gen._generate_library_headers(libraries)
        
        assert 'library std;' in headers
        assert 'use std.textio.all;' in headers
        assert 'use ieee.std_logic_textio.all;' in headers

def test_library_headers_integration():
    """Integration test for library headers."""
    @HDLModule("integration_test", ports=[
        input_port("clk"),
        output_port("count", size=4)
    ])
    def test_module(mod):
        counter = HDLSignal("reg", "counter", size=4)
        mod.add(counter)
        mod.add(HDLAssignment(mod.ports[1].signal, counter))
    
    module = test_module()
    vhdl_gen = VHDLCodeGenerator()
    vhdl_code = vhdl_gen.dump_element(module)
    
    # Basic checks
    assert 'library ieee;' in vhdl_code
    assert 'entity integration_test' in vhdl_code
    assert vhdl_code.startswith('library ieee;')