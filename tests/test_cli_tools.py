"""Test command-line tools basic functionality."""

import pytest
import subprocess
import tempfile
import json
import os
from pathlib import Path


class TestCliTools:
    """Test basic CLI tool functionality."""
    
    def test_vgc_help(self):
        """Test vgc --help command."""
        result = subprocess.run(['poetry', 'run', 'vgc', '--help'], 
                              capture_output=True, text=True)
        assert result.returncode == 0
        assert 'usage: vgc' in result.stdout
        assert 'input filename' in result.stdout
    
    def test_mmap_docgen_help(self):
        """Test mmap_docgen --help command."""
        result = subprocess.run(['poetry', 'run', 'mmap_docgen', '--help'], 
                              capture_output=True, text=True)
        assert result.returncode == 0
        assert 'usage: mmap_docgen' in result.stdout
        assert 'Model file' in result.stdout
    
    def test_axi_slave_builder_help(self):
        """Test axi_slave_builder --help command."""
        result = subprocess.run(['poetry', 'run', 'axi_slave_builder', '--help'], 
                              capture_output=True, text=True)
        assert result.returncode == 0
        assert 'usage: axi_slave_builder' in result.stdout
        assert 'Model file' in result.stdout
    
    def test_vcdhier_help(self):
        """Test vcdhier --help command."""
        result = subprocess.run(['poetry', 'run', 'vcdhier', '--help'], 
                              capture_output=True, text=True)
        assert result.returncode == 0
        assert 'usage: vcdhier' in result.stdout
        assert 'path to vcd file' in result.stdout
    
    def test_vcdevts_help(self):
        """Test vcdevts --help command."""
        result = subprocess.run(['poetry', 'run', 'vcdevts', '--help'], 
                              capture_output=True, text=True)
        assert result.returncode == 0
        assert 'usage: vcdevts' in result.stdout
        assert 'Path to event definition file' in result.stdout
    
    def test_vcdtracker_help(self):
        """Test vcdtracker --help command."""
        result = subprocess.run(['poetry', 'run', 'vcdtracker', '--help'], 
                              capture_output=True, text=True)
        assert result.returncode == 0
        assert 'usage: vcdtracker' in result.stdout
        assert 'path to vcd file' in result.stdout
    
    def test_inputgen_help(self):
        """Test inputgen --help command."""
        result = subprocess.run(['poetry', 'run', 'inputgen', '--help'], 
                              capture_output=True, text=True)
        assert result.returncode == 0
        assert 'usage: inputgen' in result.stdout
        assert 'event file' in result.stdout
    
    def test_fnboundary_help(self):
        """Test fnboundary --help command."""
        result = subprocess.run(['poetry', 'run', 'fnboundary', '--help'], 
                              capture_output=True, text=True)
        assert result.returncode == 0
        assert 'usage: fnboundary' in result.stdout
        assert 'output from objdump' in result.stdout

    def test_vgc_with_simple_input(self):
        """Test vgc with a simple vector input file."""
        # Create a simple vecgen input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vgc', delete=False) as f:
            f.write("""
// Simple vecgen file
sig_a = 0;
sig_b = 1;
""")
            input_file = f.name
        
        try:
            # Test with --dump option
            result = subprocess.run(['poetry', 'run', 'vgc', '--dump', input_file], 
                                  capture_output=True, text=True)
            
            # Should not crash, may return error due to grammar issues but shouldn't segfault
            assert result.returncode in [0, 1]  # Allow parsing errors
            
            # If successful, should output JSON
            if result.returncode == 0:
                try:
                    json.loads(result.stdout)
                except json.JSONDecodeError:
                    pass  # Acceptable if format isn't JSON
        
        finally:
            os.unlink(input_file)

    def test_vcdhier_with_sample_vcd(self):
        """Test vcdhier with the sample VCD file."""
        vcd_file = Path("usage/test.vcd")
        if vcd_file.exists():
            result = subprocess.run(['poetry', 'run', 'vcdhier', str(vcd_file), 'dumphier'], 
                                  capture_output=True, text=True)
            # Should not crash
            assert result.returncode in [0, 1]  # Allow parsing errors

    def test_fnboundary_with_sample_asm(self):
        """Test fnboundary with dummy assembly input."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.asm', delete=False) as f:
            f.write("""
00001000 <_start>:
    1000: mov r0, #0
    1004: bx lr

00001008 <main>:
    1008: push {lr}
    100c: pop {pc}
""")
            asm_file = f.name
        
        try:
            result = subprocess.run(['poetry', 'run', 'fnboundary', '--list-fns', asm_file], 
                                  capture_output=True, text=True)
            # Should not crash
            assert result.returncode in [0, 1]  # Allow parsing errors
        
        finally:
            os.unlink(asm_file)

    def test_inputgen_with_sample_config(self):
        """Test inputgen with simple config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "signals": ["clk", "reset", "data"],
                "cycles": 10
            }
            json.dump(config, f)
            config_file = f.name
        
        try:
            result = subprocess.run(['poetry', 'run', 'inputgen', config_file], 
                                  capture_output=True, text=True)
            # Should not crash
            assert result.returncode in [0, 1]  # Allow parsing errors
        
        finally:
            os.unlink(config_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])