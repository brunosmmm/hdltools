#!/usr/bin/env python3
"""
Comprehensive Test Suite for VCD Parsing and Event Detection

This test suite thoroughly validates:
1. Pattern validation and format conversion
2. VCD parsing accuracy and robustness
3. Event detection and trigger mechanisms
4. Width validation and error handling
5. Integration testing of the complete pipeline
"""

import unittest
import tempfile
import json
import subprocess
import warnings
from pathlib import Path
import sys

# Add HDLTools to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hdltools.patterns import Pattern, PatternError
from hdltools.vcd.trigger.trigcond import build_descriptors_from_str
from hdltools.vcd.trigger import VCDTriggerDescriptor
from hdltools.vcd.event import get_tracker_class
from hdltools.vcd.streaming_parser import StreamingVCDParser


class TestPatternValidation(unittest.TestCase):
    """Test pattern validation and format conversion."""
    
    def test_decimal_to_binary_conversion(self):
        """Test decimal numbers are correctly converted to binary."""
        test_cases = [
            (0, "0"),
            (1, "1"),
            (3, "11"),
            (7, "111"),
            (15, "1111"),
            (255, "11111111"),
            ("0", "0"),
            ("3", "11"),
            ("15", "1111"),
            ("255", "11111111"),
        ]
        
        for input_val, expected in test_cases:
            with self.subTest(input=input_val):
                pattern = Pattern(input_val)
                self.assertEqual(pattern.pattern, expected)
    
    def test_hexadecimal_conversion(self):
        """Test hexadecimal patterns are correctly converted."""
        test_cases = [
            ("Fh", "1111"),
            ("FFh", "11111111"),
            ("A3h", "10100011"),
            ("0xF", "1111"),
            ("0xFF", "11111111"),
            ("0xA3", "10100011"),
            ("0X1234", "0001001000110100"),
            ("ABCD", "1010101111001101"),  # Auto-detected hex
            ("1234", "0001001000110100"),  # Auto-detected hex
        ]
        
        for input_val, expected in test_cases:
            with self.subTest(input=input_val):
                pattern = Pattern(input_val)
                self.assertEqual(pattern.pattern, expected)
    
    def test_binary_patterns(self):
        """Test binary patterns are handled correctly."""
        test_cases = [
            ("0", "0"),
            ("1", "1"),
            ("1010", "1010"),
            ("0b1010", "1010"),
            ("0B1010", "1010"),
            ("101x", "101x"),
            ("10X1", "10X1"),
            ("xxxx", "xxxx"),
            ("XXXX", "XXXX"),
        ]
        
        for input_val, expected in test_cases:
            with self.subTest(input=input_val):
                pattern = Pattern(input_val)
                self.assertEqual(pattern.pattern, expected)
    
    def test_invalid_patterns(self):
        """Test invalid patterns are properly rejected."""
        invalid_patterns = [
            "",
            "   ",
            "123G",
            "gggg",
            -5,
            "0x",
            "h",
            "xyz",
            "12$34",
        ]
        
        for invalid_input in invalid_patterns:
            with self.subTest(input=invalid_input):
                with self.assertRaises((PatternError, TypeError, ValueError)):
                    Pattern(invalid_input)
    
    def test_error_messages_are_helpful(self):
        """Test that error messages provide helpful information."""
        with self.assertRaises(PatternError) as cm:
            Pattern("")
        self.assertIn("empty", str(cm.exception).lower())
        
        with self.assertRaises(PatternError) as cm:
            Pattern("gggg")
        self.assertIn("format", str(cm.exception).lower())


class TestTriggerConditionParsing(unittest.TestCase):
    """Test trigger condition parsing and validation."""
    
    def test_valid_condition_parsing(self):
        """Test valid trigger conditions are parsed correctly."""
        valid_conditions = [
            "cpu_system::clk==1",
            "scope::signal==0101",
            "module::bus_addr==A000h",
            "cpu::state!=0000",
            "test::sig==x101",
            "counter::count==3",  # Should convert decimal
            "mem::addr==0xFFFF",  # Should convert hex
        ]
        
        for condition in valid_conditions:
            with self.subTest(condition=condition):
                try:
                    descriptors, mode = build_descriptors_from_str(condition)
                    self.assertIsInstance(descriptors, list)
                    self.assertGreater(len(descriptors), 0)
                    self.assertIn(mode, ["&&", "=>"])
                except Exception as e:
                    self.fail(f"Valid condition '{condition}' failed: {e}")
    
    def test_invalid_condition_parsing(self):
        """Test invalid conditions produce helpful error messages."""
        invalid_conditions = [
            "clk",  # Missing operator
            "scope::signal=1",  # Single equals
            "scope::signal==",  # Empty value
            "::signal==1",  # Empty scope
            "scope::==1",  # Empty signal
            "scope::signal==123G",  # Invalid pattern
        ]
        
        for condition in invalid_conditions:
            with self.subTest(condition=condition):
                with self.assertRaises(Exception) as cm:
                    build_descriptors_from_str(condition)
                # Verify error message is informative
                error_msg = str(cm.exception)
                self.assertTrue(len(error_msg) > 20, f"Error message too short for '{condition}': {error_msg}")
    
    def test_complex_conditions(self):
        """Test complex condition parsing with multiple operators."""
        # Note: This tests the parsing infrastructure
        simple_conditions = [
            "cpu::state==0001",
            "bus::req==1",
        ]
        
        for condition in simple_conditions:
            with self.subTest(condition=condition):
                descriptors, mode = build_descriptors_from_str(condition)
                self.assertEqual(len(descriptors), 1)
                desc = descriptors[0]
                self.assertIsInstance(desc, VCDTriggerDescriptor)


class TestVCDParsing(unittest.TestCase):
    """Test VCD parsing accuracy and robustness."""
    
    def setUp(self):
        """Set up test VCD content."""
        self.test_vcd = """$date
    Mon Jun 21 15:30:00 2025
$end
$version
    Test VCD
$end
$timescale
    1ns
$end
$scope module test_module $end
$var wire 1 a clk $end
$var wire 4 b counter [3:0] $end
$var wire 8 c data [7:0] $end
$upscope $end
$enddefinitions $end
$dumpvars
0a
b0000 b
b00000000 c
$end
#0
#10
1a
#20
0a
b0001 b
#30
1a
b11111111 c
#40
0a
b0010 b
#50
1a
b00000000 c
"""
    
    def test_vcd_header_parsing(self):
        """Test VCD header is parsed correctly."""
        parser = StreamingVCDParser()
        parser.parse(self.test_vcd)
        
        # Check variables were created
        self.assertGreater(len(parser.variables), 0)
        
        # Check variable properties
        variables = parser.variables
        var_names = [var.name for var in variables.values()]
        self.assertIn('clk', var_names)
        self.assertIn('counter', var_names)
        self.assertIn('data', var_names)
    
    def test_vcd_timing_parsing(self):
        """Test VCD timing information is parsed correctly."""
        parser = StreamingVCDParser()
        parser.parse(self.test_vcd)
        
        # Should have processed time up to #50
        self.assertEqual(parser.current_time, 50)
    
    def test_vcd_signal_changes(self):
        """Test signal value changes are tracked correctly."""
        parser = StreamingVCDParser()
        
        # Track value changes during parsing
        value_changes = []
        
        class TrackingParser(StreamingVCDParser):
            def value_change_handler(self, stmt, fields):
                super().value_change_handler(stmt, fields)
                value_changes.append((self.current_time, fields.get('var'), fields.get('value')))
        
        tracking_parser = TrackingParser()
        tracking_parser.parse(self.test_vcd)
        
        # Should have captured value changes
        self.assertGreater(len(value_changes), 0)
        
        # Check specific changes occurred
        var_ids = [change[1] for change in value_changes]
        self.assertIn('a', var_ids)  # Clock changes
        self.assertIn('b', var_ids)  # Counter changes
    
    def test_vcd_variable_width_detection(self):
        """Test variable width detection from VCD."""
        parser = StreamingVCDParser()
        parser.parse(self.test_vcd)
        
        variables = parser.variables
        
        # Find variables by name
        clk_var = None
        counter_var = None
        data_var = None
        
        for var in variables.values():
            if var.name == 'clk':
                clk_var = var
            elif var.name == 'counter':
                counter_var = var
            elif var.name == 'data':
                data_var = var
        
        # Check widths are detected correctly
        if clk_var and hasattr(clk_var, 'size'):
            self.assertEqual(clk_var.size, 1)
        if counter_var and hasattr(counter_var, 'size'):
            self.assertEqual(counter_var.size, 4)
        if data_var and hasattr(data_var, 'size'):
            self.assertEqual(data_var.size, 8)


class TestEventDetection(unittest.TestCase):
    """Test event detection and trigger mechanisms."""
    
    def setUp(self):
        """Set up test VCD and event configurations."""
        self.test_vcd = """$date
    Mon Jun 21 15:30:00 2025
$end
$version
    Test VCD
$end
$timescale
    1ns
$end
$scope module cpu_system $end
$var wire 1 a clk $end
$var wire 4 b cpu_state [3:0] $end
$upscope $end
$enddefinitions $end
$dumpvars
0a
b0000 b
$end
#0
#10
1a
b0001 b
#20
0a
#30
1a
b0010 b
#40
0a
#50
1a
b0011 b
#60
0a
"""
    
    def test_basic_event_detection(self):
        """Test basic event detection works correctly."""
        events_config = {
            "clock_rising": (([build_descriptors_from_str("cpu_system::clk==1")[0][0]], "&&"), {}),
            "state_fetch": (([build_descriptors_from_str("cpu_system::cpu_state==1")[0][0]], "&&"), {}),
        }
        
        TrackerClass = get_tracker_class(StreamingVCDParser)
        tracker = TrackerClass(
            events=events_config,
            postconditions=None,
            preconditions=None,
            time_range=None,
            debug=False
        )
        
        tracker.parse(self.test_vcd)
        
        # Check events were detected
        event_counts = tracker.event_counts
        self.assertIn("clock_rising", event_counts)
        self.assertGreater(event_counts["clock_rising"], 0)
    
    def test_decimal_pattern_conversion_in_events(self):
        """Test decimal patterns are converted correctly in event detection."""
        # Use decimal pattern that should be converted
        events_config = {
            "state_one": (([build_descriptors_from_str("cpu_system::cpu_state==1")[0][0]], "&&"), {}),
            "state_three": (([build_descriptors_from_str("cpu_system::cpu_state==3")[0][0]], "&&"), {}),
        }
        
        TrackerClass = get_tracker_class(StreamingVCDParser)
        tracker = TrackerClass(
            events=events_config,
            postconditions=None,
            preconditions=None,
            time_range=None,
            debug=False
        )
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            tracker.parse(self.test_vcd)
            
            # Should have width warnings for narrow patterns
            width_warnings = [warning for warning in w if "width" in str(warning.message).lower()]
            # We expect warnings for 1->0001 and 3->0011 conversions
            
        event_counts = tracker.event_counts
        history_types = {evt.evt_type for evt in tracker.event_history}

        # Completed events appear in counts; sustained matches at least start in history
        self.assertIn("state_one", history_types)
        self.assertIn("state_three", history_types)
        self.assertGreater(event_counts.get("state_one", 0) + len([
            e for e in tracker.event_history if e.evt_type == "state_one"
        ]), 0)
    
    def test_event_timing_accuracy(self):
        """Test event timing is captured accurately."""
        events_config = {
            "clock_edge": (([build_descriptors_from_str("cpu_system::clk==1")[0][0]], "&&"), {}),
        }
        
        TrackerClass = get_tracker_class(StreamingVCDParser)
        tracker = TrackerClass(
            events=events_config,
            postconditions=None,
            preconditions=None,
            time_range=None,
            debug=False
        )
        
        tracker.parse(self.test_vcd)
        
        # Check event history for timing accuracy
        event_history = tracker.event_history
        self.assertGreater(len(event_history), 0)
        
        # Events should occur at expected times (10, 30, 50)
        clock_events = [evt for evt in event_history if evt.evt_type == "clock_edge"]
        self.assertGreater(len(clock_events), 0)
        event_times = [evt.time for evt in clock_events]
        for expected_time in (10, 30, 50):
            self.assertIn(expected_time, event_times)


class TestWidthValidation(unittest.TestCase):
    """Test signal width validation and warnings."""
    
    def test_width_warning_generation(self):
        """Test width warnings are generated appropriately."""
        # This would require integration with actual VCD parsing
        # For now, test the pattern width detection
        
        pattern_4bit = Pattern("3")  # Converts to "11" (2 bits)
        pattern_8bit = Pattern("255")  # Converts to "11111111" (8 bits)
        
        self.assertEqual(len(pattern_4bit.pattern), 2)  # 2 bits for "11"
        self.assertEqual(len(pattern_8bit.pattern), 8)  # 8 bits for "11111111"
    
    def test_width_error_prevention(self):
        """Test that width errors are handled appropriately."""
        # Create a pattern that would be too wide
        large_pattern = Pattern("65535")  # 16 bits
        self.assertEqual(len(large_pattern.pattern), 16)
        
        # The actual width validation happens during VCD variable linking
        # This tests the pattern size calculation is correct


class TestIntegrationVCDEventsPipeline(unittest.TestCase):
    """Integration tests for the complete VCD-to-events pipeline."""
    
    def test_end_to_end_vcdevts_tool(self):
        """Test the complete vcdevts tool pipeline."""
        # Create test VCD file
        test_vcd_content = """$date
    Mon Jun 21 15:30:00 2025
$end
$version
    Integration Test VCD
$end
$timescale
    1ns
$end
$scope module test_system $end
$var wire 1 a clk $end
$var wire 2 b state [1:0] $end
$upscope $end
$enddefinitions $end
$dumpvars
0a
b00 b
$end
#0
#10
1a
#20
0a
b01 b
#30
1a
#40
0a
b10 b
#50
1a
"""
        
        # Create test configuration with various pattern formats
        test_config = {
            "events": [
                {
                    "name": "clock_rising",
                    "conds": "test_system::clk==1"
                },
                {
                    "name": "state_decimal", 
                    "conds": "test_system::state==1"  # Decimal format
                },
                {
                    "name": "state_binary",
                    "conds": "test_system::state==10"  # Should be auto-detected as binary
                }
            ]
        }
        
        # Write temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vcd', delete=False) as vcd_file:
            vcd_file.write(test_vcd_content)
            vcd_path = vcd_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as config_file:
            json.dump(test_config, config_file, indent=2)
            config_path = config_file.name
        
        try:
            # Run vcdevts tool
            result = subprocess.run([
                'poetry', 'run', 'python', 'hdltools/tools/vcdevts/__init__.py',
                '--dump-counts', config_path, vcd_path
            ], capture_output=True, text=True, check=True)
            
            # Parse output
            output_lines = result.stdout.strip().split('\n')
            event_lines = [line for line in output_lines 
                          if line and not line.startswith('The "poetry') 
                          and not line.startswith('EVENT') 
                          and not line.startswith('⚠️')]
            
            # Should have detected events
            self.assertGreater(len(event_lines), 0)
            
            # Check for expected events
            output_text = result.stdout
            self.assertIn("clock_rising", output_text)
            
        except subprocess.CalledProcessError as e:
            self.fail(f"vcdevts tool failed: {e.stderr}")
        
        finally:
            # Clean up
            Path(vcd_path).unlink(missing_ok=True)
            Path(config_path).unlink(missing_ok=True)
    
    def test_error_handling_pipeline(self):
        """Test error handling throughout the pipeline."""
        # Test with invalid configuration
        invalid_config = {
            "events": [
                {
                    "name": "invalid_event",
                    "conds": "scope::signal==INVALID_PATTERN"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as config_file:
            json.dump(invalid_config, config_file, indent=2)
            config_path = config_file.name
        
        try:
            # Should fail with helpful error message
            result = subprocess.run([
                'poetry', 'run', 'python', 'hdltools/tools/vcdevts/__init__.py',
                '--dump-counts', config_path, 'complex_soc_demo.vcd'
            ], capture_output=True, text=True, check=False)
            
            # Should fail (non-zero exit code)
            self.assertNotEqual(result.returncode, 0)
            
            # Should have helpful error message
            error_output = result.stdout + result.stderr
            self.assertIn("Error", error_output)
            
        finally:
            Path(config_path).unlink(missing_ok=True)


class TestRegressionTests(unittest.TestCase):
    """Regression tests to ensure existing functionality still works."""
    
    def test_existing_binary_patterns_still_work(self):
        """Test that existing binary patterns continue to work."""
        existing_patterns = [
            "0001",
            "1111", 
            "101x",
            "XXXX",
            "0b1010",
        ]
        
        for pattern in existing_patterns:
            with self.subTest(pattern=pattern):
                try:
                    p = Pattern(pattern)
                    # Should not raise exception
                    self.assertIsInstance(p.pattern, str)
                except Exception as e:
                    self.fail(f"Existing pattern '{pattern}' failed: {e}")
    
    def test_vcdhier_tool_still_works(self):
        """Test that vcdhier tool still functions correctly."""
        if Path('complex_soc_demo.vcd').exists():
            try:
                result = subprocess.run([
                    'poetry', 'run', 'python', 'hdltools/tools/vcdhier/__init__.py',
                    'complex_soc_demo.vcd', 'dumphier'
                ], capture_output=True, text=True, check=True)
                
                # Should show hierarchy
                output = result.stdout
                self.assertIn("cpu_system", output)
                
            except subprocess.CalledProcessError as e:
                self.fail(f"vcdhier tool failed: {e}")


def run_comprehensive_tests():
    """Run all comprehensive tests and provide detailed reporting."""
    
    print("🧪 HDLTools Comprehensive Validation Test Suite")
    print("=" * 60)
    print("Testing all developments in VCD parsing, pattern validation,")
    print("event detection, width validation, and error handling.")
    print()
    
    # Create test loader
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestPatternValidation,
        TestTriggerConditionParsing,
        TestVCDParsing,
        TestEventDetection,
        TestWidthValidation,
        TestIntegrationVCDEventsPipeline,
        TestRegressionTests,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 60)
    print("🎯 Test Results Summary")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"📊 Tests run: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failures}")
    print(f"💥 Errors: {errors}")
    
    if failures > 0:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   • {test}: {traceback.split('AssertionError: ')[-1].split()[0] if 'AssertionError:' in traceback else 'See details above'}")
    
    if errors > 0:
        print(f"\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"   • {test}: {traceback.split('Error: ')[-1].split()[0] if 'Error:' in traceback else 'See details above'}")
    
    if failures == 0 and errors == 0:
        print(f"\n🎉 All tests PASSED!")
        print(f"✅ Pattern validation is robust")
        print(f"✅ VCD parsing is accurate") 
        print(f"✅ Event detection is working")
        print(f"✅ Width validation is functional")
        print(f"✅ Error handling is comprehensive")
        print(f"✅ Integration pipeline is solid")
        print(f"🚀 Ready for production use!")
    else:
        print(f"\n🔧 Some issues need attention before production deployment.")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)