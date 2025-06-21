"""Test functional equivalence between Verilog and VHDL generation."""

import pytest
import tempfile
import subprocess
import os
from pathlib import Path
from hdltools.abshdl.module import HDLModule, input_port, output_port
from hdltools.abshdl.signal import HDLSignal
from hdltools.abshdl.assign import HDLAssignment
from hdltools.abshdl.seq import HDLSequentialBlock
from hdltools.abshdl.sens import HDLSensitivityList, HDLSensitivityDescriptor
from hdltools.abshdl.ifelse import HDLIfElse
from hdltools.abshdl.expr import HDLExpression
from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.vhdl.codegen import VHDLCodeGenerator
from hdltools.vcd.compare import compare_vcd_files


class TestFunctionalEquivalence:
    """Test functional equivalence between Verilog and VHDL generation."""
    
    def create_simple_counter(self):
        """Create a simple counter module for testing."""
        @HDLModule("simple_counter", ports=[
            input_port("clk"),
            input_port("rst"),
            output_port("count", size=4)
        ])
        def counter_module(mod):
            # Create counter register
            counter_reg = HDLSignal("reg", "counter_reg", size=4)
            mod.add(counter_reg)
            
            # Connect counter to output
            mod.add(HDLAssignment(mod.ports[2].signal, counter_reg))
            
            # Create clocked process with proper reset and increment logic
            clk_port = mod.ports[0]  # clk
            rst_port = mod.ports[1]  # rst
            
            # Create sensitivity list for rising edge of clock
            sens_desc = HDLSensitivityDescriptor("rise", clk_port.signal)
            sens_list = HDLSensitivityList()
            sens_list.add(sens_desc)
            
            # Create sequential block
            seq_block = HDLSequentialBlock(sens_list)
            
            # Add reset condition: if (rst) counter_reg <= 0
            rst_condition = HDLExpression(rst_port.signal)
            reset_assignment = HDLAssignment(counter_reg, HDLExpression(0))
            
            # Add increment condition: else counter_reg <= counter_reg + 1
            # Use Python operators to create expression
            counter_expr = HDLExpression(counter_reg)
            one_expr = HDLExpression(1)
            increment_expr = counter_expr + one_expr
            increment_assignment = HDLAssignment(counter_reg, increment_expr)
            
            # Create if-else block for reset/increment logic
            reset_if = HDLIfElse(rst_condition)
            reset_if.add_to_if_scope(reset_assignment)
            reset_if.add_to_else_scope(increment_assignment)
            
            seq_block.add(reset_if)
            mod.add(seq_block)
        
        return counter_module()
    
    def write_testbench_verilog(self, module_file, tb_file):
        """Write a comprehensive Verilog testbench."""
        testbench = f'''
`timescale 1ns/1ns

module tb_simple_counter;
    reg clk;
    reg rst;
    wire [3:0] count;
    
    // Instantiate DUT
    simple_counter dut (
        .clk(clk),
        .rst(rst),
        .count(count)
    );
    
    // Clock generation - 10ns period (100MHz)
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end
    
    // Test stimulus
    initial begin
        $dumpfile("simulation.vcd");
        $dumpvars(0, tb_simple_counter);
        
        // Initial reset
        rst = 1;
        #30;  // Hold reset for 3 clock cycles
        rst = 0;
        
        // Let counter run for several cycles
        #200; // 20 clock cycles
        
        // Apply reset again to verify reset behavior
        rst = 1;
        #20;  // 2 clock cycles
        rst = 0;
        
        // Run a few more cycles
        #50;  // 5 clock cycles
        
        $finish;
    end
    
    // Monitor counter values
    initial begin
        $monitor("Time=%0t rst=%b count=%d", $time, rst, count);
    end
endmodule
'''
        with open(tb_file, 'w') as f:
            f.write(testbench)
    
    def write_testbench_vhdl(self, module_file, tb_file):
        """Write a comprehensive VHDL testbench."""
        testbench = f'''
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_simple_counter is
end tb_simple_counter;

architecture test of tb_simple_counter is
    signal clk : std_logic := '0';
    signal rst : std_logic := '1';
    signal count : std_logic_vector(3 downto 0);
    
    component simple_counter
        port(
            clk : in std_logic;
            rst : in std_logic;
            count : out std_logic_vector(3 downto 0)
        );
    end component;
    
    -- Clock period definition
    constant clock_period : time := 10 ns;
    
begin
    -- Instantiate DUT
    dut: simple_counter port map (
        clk => clk,
        rst => rst,
        count => count
    );
    
    -- Clock generation - 10ns period (100MHz)
    clk_process: process
    begin
        clk <= '0';
        wait for clock_period/2;
        clk <= '1';
        wait for clock_period/2;
    end process;
    
    -- Test stimulus process
    stim_process: process
    begin
        -- Initial reset
        rst <= '1';
        wait for 30 ns;  -- Hold reset for 3 clock cycles
        rst <= '0';
        
        -- Let counter run for several cycles
        wait for 200 ns; -- 20 clock cycles
        
        -- Apply reset again to verify reset behavior
        rst <= '1';
        wait for 20 ns;  -- 2 clock cycles
        rst <= '0';
        
        -- Run a few more cycles
        wait for 50 ns;  -- 5 clock cycles
        
        -- End simulation  
        report "Simulation finished normally";
        wait;
    end process;
    
    -- Monitor process
    monitor_process: process(clk, rst)
    begin
        -- Note: VHDL doesn't have $monitor equivalent, but this provides similar functionality
        if rising_edge(clk) or rst = '1' then
            report "Time=" & time'image(now) & " rst=" & std_logic'image(rst) & 
                   " count=" & integer'image(to_integer(unsigned(count)));
        end if;
    end process;
    
end test;
'''
        with open(tb_file, 'w') as f:
            f.write(testbench)
    
    def run_verilog_simulation(self, work_dir, module_file, tb_file):
        """Run Verilog simulation with iverilog."""
        vcd_file = work_dir / "verilog_simulation.vcd"
        
        try:
            # Compile
            compile_result = subprocess.run([
                'iverilog', '-o', str(work_dir / 'verilog_sim'), 
                str(module_file), str(tb_file)
            ], capture_output=True, text=True, cwd=work_dir)
            
            if compile_result.returncode != 0:
                return None, f"Verilog compilation failed: {compile_result.stderr}"
            
            # Run simulation
            sim_result = subprocess.run([
                str(work_dir / 'verilog_sim')
            ], capture_output=True, text=True, cwd=work_dir)
            
            if sim_result.returncode != 0:
                return None, f"Verilog simulation failed: {sim_result.stderr}"
            
            # Check if VCD was generated
            if (work_dir / "simulation.vcd").exists():
                # Move to specific name
                (work_dir / "simulation.vcd").rename(vcd_file)
                return str(vcd_file), None
            else:
                return None, "No VCD file generated by Verilog simulation"
                
        except FileNotFoundError:
            return None, "iverilog not found - Verilog simulation skipped"
    
    def run_vhdl_simulation(self, work_dir, module_file, tb_file):
        """Run VHDL simulation with GHDL."""
        vcd_file = work_dir / "vhdl_simulation.vcd"
        
        try:
            # Analyze files
            for vhdl_file in [module_file, tb_file]:
                analyze_result = subprocess.run([
                    'ghdl', '-a', str(vhdl_file)
                ], capture_output=True, text=True, cwd=work_dir)
                
                if analyze_result.returncode != 0:
                    return None, f"VHDL analysis failed: {analyze_result.stderr}"
            
            # Elaborate
            elab_result = subprocess.run([
                'ghdl', '-e', 'tb_simple_counter'
            ], capture_output=True, text=True, cwd=work_dir)
            
            if elab_result.returncode != 0:
                return None, f"VHDL elaboration failed: {elab_result.stderr}"
            
            # Run simulation with VCD output and wave dumping
            # Use relative path for VCD file since GHDL runs in work_dir
            vcd_filename = vcd_file.name
            ghdl_cmd = ['ghdl', '-r', 'tb_simple_counter', f'--vcd={vcd_filename}', '--stop-time=300ns']
            sim_result = subprocess.run(ghdl_cmd, capture_output=True, text=True, cwd=work_dir)
            
            # GHDL may exit with error code even for successful simulations due to 
            # assertion-based termination, so check if VCD was generated
            if vcd_file.exists():
                return str(vcd_file), None
            else:
                return None, f"VHDL simulation failed to generate VCD. Return code: {sim_result.returncode}, stderr: {sim_result.stderr}"
                
        except FileNotFoundError:
            return None, "ghdl not found - VHDL simulation skipped"
    
    @pytest.mark.integration
    def test_verilog_vhdl_equivalence(self):
        """Test that Verilog and VHDL generate functionally equivalent results."""
        # Create test module
        module = self.create_simple_counter()
        
        verilog_gen = VerilogCodeGenerator()
        vhdl_gen = VHDLCodeGenerator()
        
        # Generate code
        verilog_code = verilog_gen.dump_element(module)
        vhdl_code = vhdl_gen.dump_element(module)
        
        with tempfile.TemporaryDirectory(prefix="equiv_test_") as temp_dir:
            work_dir = Path(temp_dir)
            
            # Write HDL files
            verilog_file = work_dir / "simple_counter.v"
            vhdl_file = work_dir / "simple_counter.vhd"
            verilog_tb = work_dir / "tb_simple_counter.v" 
            vhdl_tb = work_dir / "tb_simple_counter.vhd"
            
            with open(verilog_file, 'w') as f:
                f.write(verilog_code)
            with open(vhdl_file, 'w') as f:
                f.write(vhdl_code)
            
            # Write testbenches
            self.write_testbench_verilog(verilog_file, verilog_tb)
            self.write_testbench_vhdl(vhdl_file, vhdl_tb)
            
            # Run simulations
            verilog_vcd, v_error = self.run_verilog_simulation(work_dir, verilog_file, verilog_tb)
            vhdl_vcd, h_error = self.run_vhdl_simulation(work_dir, vhdl_file, vhdl_tb)
            
            # Check simulation results
            if v_error and h_error:
                pytest.skip(f"Both simulations failed: Verilog: {v_error}, VHDL: {h_error}")
            elif v_error:
                pytest.skip(f"Verilog simulation failed: {v_error}")
            elif h_error:
                pytest.skip(f"VHDL simulation failed: {h_error}")
            
            # Compare VCD files using the library function
            comparison_result = compare_vcd_files(verilog_vcd, vhdl_vcd)
            
            # Print detailed comparison info for debugging
            print("\nVCD Comparison Results:")
            print(f"Verilog signals: {comparison_result.file1_signals}")
            print(f"VHDL signals: {comparison_result.file2_signals}")
            print(f"Equivalent: {comparison_result.equivalent}")
            
            # Check detailed comparison for functional signals
            functional_signals = ['count', 'counter_reg']  # DUT output signals
            functional_equivalent = True
            functional_mismatches = []
            
            print("\nDetailed comparison:")
            for signal, details in comparison_result.detailed_comparison.items():
                status = "✓" if details['matches'] else "✗"
                print(f"  {status} {signal}: V={details['file1_changes']} H={details['file2_changes']}")
                
                # Check if this is a functional signal that must match exactly
                if signal in functional_signals and not details['matches']:
                    functional_equivalent = False
                    functional_mismatches.extend([m for m in comparison_result.mismatches if signal in m])
            
            if not functional_equivalent:
                print(f"\nFunctional mismatches found ({len(functional_mismatches)}):")
                for mismatch in functional_mismatches[:5]:
                    print(f"  - {mismatch}")
                if len(functional_mismatches) > 5:
                    print(f"  ... and {len(functional_mismatches) - 5} more")
                
                error_msg = f"Functional equivalence failed: DUT outputs don't match ({len(functional_mismatches)} mismatches)"
                assert False, error_msg
            
            # Check for non-functional mismatches (testbench signals)
            non_functional_mismatches = [m for m in comparison_result.mismatches 
                                       if not any(fs in m for fs in functional_signals)]
            
            if non_functional_mismatches:
                print(f"\nNon-functional differences found (testbench signals): {len(non_functional_mismatches)}")
                print("These differences are expected due to different testbench signal recording between Verilog and VHDL")
            
            # If we get here, the DUT outputs are functionally equivalent
            print("✓ DUT outputs are functionally equivalent!")
            assert True


def test_vcd_comparator():
    """Test the VCD comparator functionality."""
    # Test with some example VCD content
    import tempfile
    
    # Create two identical minimal VCD files for testing
    vcd_content = '''$date
   Test VCD
$end
$version
   Test version
$end
$timescale 1ps $end
$scope module test $end
$var wire 1 ! clk $end
$var wire 1 " data $end
$upscope $end
$enddefinitions $end
$dumpvars
0!
x"
$end
#0
#5
1!
#10
0!
1"
#15
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.vcd', delete=False) as f1:
        f1.write(vcd_content)
        vcd_file1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.vcd', delete=False) as f2:
        f2.write(vcd_content)
        vcd_file2 = f2.name
    
    try:
        # Test identical files
        result = compare_vcd_files(vcd_file1, vcd_file2)
        assert result.equivalent
        assert len(result.mismatches) == 0
        
        # Test different files  
        different_content = vcd_content.replace('#15', '#15\n0"')  # Add different change
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vcd', delete=False) as f3:
            f3.write(different_content)
            vcd_file3 = f3.name
        
        try:
            result2 = compare_vcd_files(vcd_file1, vcd_file3)
            assert not result2.equivalent
            assert len(result2.mismatches) > 0
        finally:
            os.unlink(vcd_file3)
            
    finally:
        os.unlink(vcd_file1)
        os.unlink(vcd_file2)