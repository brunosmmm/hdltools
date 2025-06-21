"""Test VCD comparison with manually created files."""

import pytest
import tempfile
import os
from pathlib import Path
from hdltools.vcd.compare import compare_vcd_files


def create_test_vcd(filename, count_sequence):
    """Create a test VCD file with a specific count sequence."""
    vcd_content = f'''$date
    Test VCD for functional verification
$end
$version
    HDLTools Test Generator
$end
$timescale 1ns $end
$scope module tb_simple_counter $end
$var wire 1 ! clk $end
$var wire 1 " rst $end
$var wire 4 # count $end
$upscope $end
$enddefinitions $end
$dumpvars
0!
1"
b0000 #
$end
'''
    
    time_step = 0
    for i, (clk, rst, count) in enumerate(count_sequence):
        vcd_content += f"#{time_step}\n"
        vcd_content += f"{clk}!\n"
        vcd_content += f"{rst}\"\n"
        vcd_content += f"b{count:04b} #\n"
        time_step += 5
    
    with open(filename, 'w') as f:
        f.write(vcd_content)


def test_identical_vcd_files():
    """Test that identical VCD files are detected as equivalent."""
    count_sequence = [
        (0, 1, 0),  # Reset asserted
        (1, 1, 0),  # Clock edge, still reset
        (0, 1, 0),  # Clock low
        (1, 0, 0),  # Release reset, should stay 0
        (0, 0, 0),  # Clock low
        (1, 0, 1),  # First increment
        (0, 0, 1),  # Clock low
        (1, 0, 2),  # Second increment
        (0, 0, 2),  # Clock low
        (1, 0, 3),  # Third increment
    ]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        vcd1 = os.path.join(temp_dir, "test1.vcd")
        vcd2 = os.path.join(temp_dir, "test2.vcd")
        
        create_test_vcd(vcd1, count_sequence)
        create_test_vcd(vcd2, count_sequence)
        
        result = compare_vcd_files(vcd1, vcd2)
        
        assert result.equivalent
        assert len(result.mismatches) == 0
        assert 'clk' in result.file1_signals
        assert 'rst' in result.file1_signals
        assert 'count' in result.file1_signals


def test_different_vcd_files():
    """Test that different VCD files are detected as not equivalent."""
    count_sequence1 = [
        (0, 1, 0),  # Reset
        (1, 0, 0),  # Release reset
        (0, 0, 0),
        (1, 0, 1),  # Increment to 1
        (0, 0, 1),
        (1, 0, 2),  # Increment to 2
    ]
    
    count_sequence2 = [
        (0, 1, 0),  # Reset
        (1, 0, 0),  # Release reset  
        (0, 0, 0),
        (1, 0, 1),  # Increment to 1
        (0, 0, 1),
        (1, 0, 3),  # Different! Should be 2 but shows 3
    ]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        vcd1 = os.path.join(temp_dir, "correct.vcd")
        vcd2 = os.path.join(temp_dir, "incorrect.vcd")
        
        create_test_vcd(vcd1, count_sequence1)
        create_test_vcd(vcd2, count_sequence2)
        
        result = compare_vcd_files(vcd1, vcd2)
        
        assert not result.equivalent
        assert len(result.mismatches) > 0
        
        # Should have a mismatch in the count signal
        mismatch_found = any('count' in mismatch for mismatch in result.mismatches)
        assert mismatch_found, f"Expected count mismatch not found in: {result.mismatches}"


def test_time_offset_tolerance():
    """Test that small timing differences within tolerance are ignored."""
    # Create two sequences with slightly different timing
    with tempfile.TemporaryDirectory() as temp_dir:
        vcd1_content = '''$date
    Test VCD 1
$end
$timescale 1ns $end
$scope module test $end
$var wire 1 ! clk $end
$upscope $end
$enddefinitions $end
$dumpvars
0!
$end
#0
0!
#10
1!
#20
0!
'''
        
        vcd2_content = '''$date
    Test VCD 2  
$end
$timescale 1ns $end
$scope module test $end
$var wire 1 ! clk $end
$upscope $end
$enddefinitions $end
$dumpvars
0!
$end
#0
0!
#10
1!
#20
0!
'''
        
        vcd1 = os.path.join(temp_dir, "timing1.vcd")
        vcd2 = os.path.join(temp_dir, "timing2.vcd")
        
        with open(vcd1, 'w') as f:
            f.write(vcd1_content)
        with open(vcd2, 'w') as f:
            f.write(vcd2_content)
        
        # Should be equivalent with default tolerance
        result = compare_vcd_files(vcd1, vcd2, time_tolerance=1e-9)
        assert result.equivalent


def test_streaming_mode():
    """Test that streaming mode works for larger files."""
    # Create a longer sequence to test streaming
    long_sequence = []
    for i in range(50):
        long_sequence.extend([
            (0, 0, i % 16),
            (1, 0, i % 16),
        ])
    
    with tempfile.TemporaryDirectory() as temp_dir:
        vcd1 = os.path.join(temp_dir, "long1.vcd")
        vcd2 = os.path.join(temp_dir, "long2.vcd")
        
        create_test_vcd(vcd1, long_sequence)
        create_test_vcd(vcd2, long_sequence)
        
        # Force streaming mode
        result = compare_vcd_files(vcd1, vcd2, use_streaming=True)
        
        assert result.equivalent
        assert len(result.mismatches) == 0


def test_vcd_comparison_summary():
    """Test the comparison result summary functionality."""
    count_sequence1 = [(0, 1, 0), (1, 0, 1)]
    count_sequence2 = [(0, 1, 0), (1, 0, 2)]  # Different count
    
    with tempfile.TemporaryDirectory() as temp_dir:
        vcd1 = os.path.join(temp_dir, "sum1.vcd")
        vcd2 = os.path.join(temp_dir, "sum2.vcd")
        
        create_test_vcd(vcd1, count_sequence1)
        create_test_vcd(vcd2, count_sequence2)
        
        result = compare_vcd_files(vcd1, vcd2)
        
        # Test summary functionality
        assert not result.equivalent
        assert len(result.file1_signals) == 3  # clk, rst, count
        assert len(result.file2_signals) == 3
        
        # Check detailed comparison
        assert 'count' in result.detailed_comparison
        count_details = result.detailed_comparison['count']
        assert not count_details['matches']
        
        # Test string representation
        result_str = str(result)
        assert 'differ' in result_str.lower()
        assert 'mismatches' in result_str.lower()


if __name__ == "__main__":
    # Run the tests manually for debugging
    test_identical_vcd_files()
    print("✓ Identical VCD files test passed")
    
    test_different_vcd_files()
    print("✓ Different VCD files test passed")
    
    test_time_offset_tolerance()
    print("✓ Time tolerance test passed")
    
    test_streaming_mode()
    print("✓ Streaming mode test passed")
    
    test_vcd_comparison_summary()
    print("✓ Summary functionality test passed")
    
    print("\n🎉 All VCD comparison tests passed!")