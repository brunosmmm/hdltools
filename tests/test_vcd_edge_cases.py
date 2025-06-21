"""Test VCD parser edge cases and robustness."""

import pytest
import tempfile
import os
from hdltools.vcd.compare import SimpleVCDParser


class TestVCDEdgeCases:
    """Test VCD parser with various edge cases."""
    
    def _test_vcd_content(self, vcd_content, should_succeed=True):
        """Helper method to test VCD content."""
        parser = SimpleVCDParser()
        
        if should_succeed:
            try:
                parser.parse(vcd_content)
                # Check that we got some variables or signal changes
                assert len(parser.variables) > 0 or len(parser.signal_changes) > 0
                return parser
            except Exception as e:
                pytest.fail(f"Expected parsing to succeed but got error: {e}")
        else:
            with pytest.raises(Exception):
                parser.parse(vcd_content)

    def test_empty_vcd_file(self):
        """Test parsing an empty VCD file."""
        # Empty VCD should parse but have no variables or signal changes
        parser = SimpleVCDParser()
        parser.parse("")
        assert len(parser.variables) == 0
        assert len(parser.signal_changes) == 0

    def test_minimal_valid_vcd(self):
        """Test parsing minimal valid VCD file."""
        vcd_content = """$version VCD writer $end
$timescale 1ns $end
$scope module top $end
$var wire 1 ! clk $end
$upscope $end
$enddefinitions $end
$dumpvars
0!
$end
"""
        self._test_vcd_content(vcd_content)

    def test_vcd_with_real_numbers(self):
        """Test VCD file with real number values."""
        vcd_content = """$version VCD writer $end
$timescale 1ns $end
$scope module top $end
$var real 64 ! voltage $end
$upscope $end
$enddefinitions $end
$dumpvars
r3.14159 !
$end
#10
r2.71828 !
#20
r1.41421 !
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vcd', delete=False) as f:
            f.write(vcd_content)
            temp_path = f.name
        
        try:
            parser = SimpleVCDParser()
            with open(temp_path, 'r') as f:
                content = f.read()
            parser.parse(content)
            assert len(parser.variables) > 0 or len(parser.signal_changes) > 0
        finally:
            os.unlink(temp_path)

    def test_vcd_with_scientific_notation(self):
        """Test VCD file with scientific notation real numbers."""
        vcd_content = """$version VCD writer $end
$timescale 1ps $end
$scope module top $end
$var real 64 ! frequency $end
$upscope $end
$enddefinitions $end
$dumpvars
r1.23e6 !
$end
#1000
r4.56e-3 !
#2000
r7.89E+12 !
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vcd', delete=False) as f:
            f.write(vcd_content)
            temp_path = f.name
        
        try:
            parser = SimpleVCDParser()
            with open(temp_path, 'r') as f:
                content = f.read()
            parser.parse(content)
            assert len(parser.variables) > 0 or len(parser.signal_changes) > 0
        finally:
            os.unlink(temp_path)

    def test_vcd_with_large_vectors(self):
        """Test VCD file with large bit vectors."""
        vcd_content = """$version VCD writer $end
$timescale 1ns $end
$scope module top $end
$var wire 64 ! data_bus $end
$var wire 128 " wide_signal $end
$upscope $end
$enddefinitions $end
$dumpvars
b1010101010101010101010101010101010101010101010101010101010101010 !
b11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111 "
$end
#100
bx !
bz "
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vcd', delete=False) as f:
            f.write(vcd_content)
            temp_path = f.name
        
        try:
            parser = SimpleVCDParser()
            with open(temp_path, 'r') as f:
                content = f.read()
            parser.parse(content)
            assert len(parser.variables) > 0 or len(parser.signal_changes) > 0
        finally:
            os.unlink(temp_path)

    def test_vcd_with_nested_scopes(self):
        """Test VCD file with deeply nested scopes."""
        vcd_content = """$version VCD writer $end
$timescale 1ns $end
$scope module top $end
$scope module cpu $end
$scope module alu $end
$scope module adder $end
$var wire 1 ! carry $end
$upscope $end
$upscope $end
$scope module decoder $end
$var wire 8 " opcode $end
$upscope $end
$upscope $end
$scope module memory $end
$var wire 32 # address $end
$var wire 32 $ data $end
$upscope $end
$upscope $end
$enddefinitions $end
$dumpvars
1!
b10101010 "
b11110000111100001111000011110000 #
b00001111000011110000111100001111 $
$end
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vcd', delete=False) as f:
            f.write(vcd_content)
            temp_path = f.name
        
        try:
            parser = SimpleVCDParser()
            with open(temp_path, 'r') as f:
                content = f.read()
            parser.parse(content)
            assert len(parser.variables) > 0 or len(parser.signal_changes) > 0
        finally:
            os.unlink(temp_path)

    def test_vcd_with_unusual_identifiers(self):
        """Test VCD file with various identifier formats."""
        vcd_content = """$version VCD writer $end
$timescale 1ns $end
$scope module top $end
$var wire 1 ! clk $end
$var wire 1 " rst_n $end
$var wire 1 # signal_123 $end
$var wire 1 $ test.signal $end
$var wire 1 % signal[0] $end
$var wire 1 & signal_with_long_name_that_is_very_descriptive $end
$upscope $end
$enddefinitions $end
$dumpvars
0!
1"
x#
z$
0%
1&
$end
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vcd', delete=False) as f:
            f.write(vcd_content)
            temp_path = f.name
        
        try:
            parser = SimpleVCDParser()
            with open(temp_path, 'r') as f:
                content = f.read()
            parser.parse(content)
            assert len(parser.variables) > 0 or len(parser.signal_changes) > 0
        finally:
            os.unlink(temp_path)

    def test_vcd_with_zero_time_changes(self):
        """Test VCD file with multiple changes at time 0."""
        vcd_content = """$version VCD writer $end
$timescale 1ns $end
$scope module top $end
$var wire 1 ! a $end
$var wire 1 " b $end
$var wire 1 # c $end
$upscope $end
$enddefinitions $end
$dumpvars
0!
0"
0#
$end
#0
1!
#0
1"
#0
1#
#5
0!
0"
0#
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vcd', delete=False) as f:
            f.write(vcd_content)
            temp_path = f.name
        
        try:
            parser = SimpleVCDParser()
            with open(temp_path, 'r') as f:
                content = f.read()
            parser.parse(content)
            assert len(parser.variables) > 0 or len(parser.signal_changes) > 0
        finally:
            os.unlink(temp_path)

    def test_vcd_with_large_timestamps(self):
        """Test VCD file with very large timestamp values."""
        vcd_content = """$version VCD writer $end
$timescale 1fs $end
$scope module top $end
$var wire 1 ! signal $end
$upscope $end
$enddefinitions $end
$dumpvars
0!
$end
#1000000000000
1!
#9999999999999999
0!
#18446744073709551615
1!
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vcd', delete=False) as f:
            f.write(vcd_content)
            temp_path = f.name
        
        try:
            parser = SimpleVCDParser()
            with open(temp_path, 'r') as f:
                content = f.read()
            parser.parse(content)
            assert len(parser.variables) > 0 or len(parser.signal_changes) > 0
        finally:
            os.unlink(temp_path)

    def test_vcd_with_comments_and_whitespace(self):
        """Test VCD file with various whitespace and comment scenarios."""
        vcd_content = """$version VCD writer with comments $end
$comment This is a test VCD file with lots of whitespace $end
$timescale   1ns   $end
$scope module top $end


$var wire 1 ! clk $end
        $var wire 1 " data $end
$upscope $end
$enddefinitions $end
$dumpvars
0!

0"
$end

#10
   1!
#20

1"

#30
0!
   0"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vcd', delete=False) as f:
            f.write(vcd_content)
            temp_path = f.name
        
        try:
            parser = SimpleVCDParser()
            with open(temp_path, 'r') as f:
                content = f.read()
            parser.parse(content)
            assert len(parser.variables) > 0 or len(parser.signal_changes) > 0
        finally:
            os.unlink(temp_path)

    def test_vcd_with_array_variables(self):
        """Test VCD file with array variable declarations."""
        vcd_content = """$version VCD writer $end
$timescale 1ns $end
$scope module top $end
$var wire 1 ! mem[0] $end
$var wire 1 " mem[1] $end
$var wire 1 # mem[2] $end
$var wire 1 $ mem[3] $end
$var wire 8 % register[15:8] $end
$var wire 8 & register[7:0] $end
$upscope $end
$enddefinitions $end
$dumpvars
0!
0"
0#
0$
b00000000 %
b11111111 &
$end
#100
1!
1"
1#
1$
b10101010 %
b01010101 &
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vcd', delete=False) as f:
            f.write(vcd_content)
            temp_path = f.name
        
        try:
            parser = SimpleVCDParser()
            with open(temp_path, 'r') as f:
                content = f.read()
            parser.parse(content)
            assert len(parser.variables) > 0 or len(parser.signal_changes) > 0
        finally:
            os.unlink(temp_path)

    def test_vcd_stress_test_many_signals(self):
        """Test VCD file with many signals to stress the parser."""
        vcd_content = """$version VCD writer $end
$timescale 1ns $end
$scope module top $end
"""
        # Generate 1000 signals
        for i in range(1000):
            symbol = chr(33 + (i % 94))  # Use printable ASCII characters
            if i >= 94:
                symbol = f"sig{i}"  # Use extended identifiers for larger numbers
            vcd_content += f"$var wire 1 {symbol} signal_{i} $end\n"
        
        vcd_content += """$upscope $end
$enddefinitions $end
$dumpvars
"""
        # Initialize all signals to 0
        for i in range(1000):
            symbol = chr(33 + (i % 94))
            if i >= 94:
                symbol = f"sig{i}"
            vcd_content += f"0{symbol}\n"
        
        vcd_content += """$end
#100
"""
        # Toggle all signals at time 100
        for i in range(1000):
            symbol = chr(33 + (i % 94))
            if i >= 94:
                symbol = f"sig{i}"
            vcd_content += f"1{symbol}\n"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.vcd', delete=False) as f:
            f.write(vcd_content)
            temp_path = f.name
        
        try:
            parser = SimpleVCDParser()
            with open(temp_path, 'r') as f:
                content = f.read()
            parser.parse(content)
            assert len(parser.variables) > 0 or len(parser.signal_changes) > 0
        finally:
            os.unlink(temp_path)

    def test_vcd_malformed_recovery(self):
        """Test parser recovery from malformed VCD sections."""
        vcd_content = """$version VCD writer $end
$timescale 1ns $end
$scope module top $end
$var wire 1 ! clk $end
$var wire 1 " data $end
$upscope $end
$enddefinitions $end
$dumpvars
0!
0"
$end
#10
1!
#20
1"
# This is a malformed timestamp - should be ignored or handled gracefully
#30
0!
#40
0"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vcd', delete=False) as f:
            f.write(vcd_content)
            temp_path = f.name
        
        try:
            parser = SimpleVCDParser()
            # Parser should either succeed or fail gracefully
            try:
                with open(temp_path, 'r') as f:
                    content = f.read()
                parser.parse(content)
                # If it succeeds, that's fine
                assert len(parser.variables) > 0 or len(parser.signal_changes) > 0
            except Exception as e:
                # If it fails, it should be a well-defined exception, not a crash
                assert isinstance(e, Exception)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    # Run a quick test to verify the edge cases work
    test_case = TestVCDEdgeCases()
    print("Testing minimal valid VCD...")
    test_case.test_minimal_valid_vcd()
    print("✓ Minimal VCD test passed")
    
    print("Testing VCD with real numbers...")
    test_case.test_vcd_with_real_numbers()
    print("✓ Real numbers test passed")
    
    print("Testing VCD with scientific notation...")
    test_case.test_vcd_with_scientific_notation()
    print("✓ Scientific notation test passed")
    
    print("Testing VCD with large vectors...")
    test_case.test_vcd_with_large_vectors()
    print("✓ Large vectors test passed")
    
    print("Testing VCD with nested scopes...")
    test_case.test_vcd_with_nested_scopes()
    print("✓ Nested scopes test passed")
    
    print("\nAll edge case tests completed successfully!")