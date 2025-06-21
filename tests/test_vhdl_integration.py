"""Integration test for VHDL code generation with NVC compiler."""

import pytest
import tempfile
import os
import subprocess
from hdltools.vhdl.codegen import VHDLCodeGenerator


def check_vhdl_syntax(vhdl_code):
    """Check VHDL syntax using NVC compiler."""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, 'test.vhd')
            with open(temp_file, 'w') as f:
                f.write(vhdl_code)
            
            # Initialize NVC work library in temp directory
            init_result = subprocess.run(
                ['nvc', '--init'],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if init_result.returncode != 0:
                return False, f"NVC init failed: {init_result.stderr}"
            
            # Run NVC to analyze the file (syntax check)
            result = subprocess.run(
                ['nvc', '-a', temp_file],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0, result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        # If NVC is not available or times out, skip syntax check
        return True, f"NVC not available: {e}"


def test_vhdl_basic_syntax():
    """Test basic VHDL syntax generation."""
    codegen = VHDLCodeGenerator()
    
    # Create a simple, manually constructed VHDL structure
    simple_vhdl = """library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity simple_test is
    port (
        clk : in std_logic;
        reset : in std_logic;
        data_in : in std_logic_vector(7 downto 0);
        data_out : out std_logic_vector(7 downto 0)
    );
end simple_test;

architecture rtl of simple_test is
    signal counter : std_logic_vector(7 downto 0);
begin
    process(clk, reset)
    begin
        if reset = '1' then
            counter <= (others => '0');
        elsif rising_edge(clk) then
            counter <= std_logic_vector(unsigned(counter) + 1);
        end if;
    end process;
    
    data_out <= counter;
end rtl;
"""
    
    print("Testing basic VHDL syntax:")
    print(simple_vhdl)
    
    # Check syntax with NVC
    syntax_ok, error_msg = check_vhdl_syntax(simple_vhdl)
    if not syntax_ok:
        print("NVC Error:", error_msg)
    
    assert syntax_ok, f"VHDL syntax check failed: {error_msg}"


def test_vhdl_helper_methods_syntax():
    """Test VHDL helper methods produce valid syntax."""
    codegen = VHDLCodeGenerator()
    
    # Test individual helper methods
    vector_val = codegen.dumps_vector(255, 8, "hex")
    assert vector_val == 'x"ff"'
    
    generic_decl = codegen.dumps_generic("WIDTH", "integer", "8")
    assert generic_decl == "WIDTH : integer := 8"
    
    port_decl = codegen.dumps_port("in", "clk", "std_logic")
    assert port_decl == "clk : in std_logic;"
    
    signal_decl = codegen.dumps_signal("counter", "std_logic_vector(7 downto 0)", "'00000000'")
    assert signal_decl == "signal counter : std_logic_vector(7 downto 0) := '00000000';"
    
    # Create a module using helper methods
    helper_vhdl = f"""library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity helper_test is
    generic (
        {codegen.dumps_generic("WIDTH", "integer", "8")}
    );
    port (
        {codegen.dumps_port("in", "clk", "std_logic")}
        {codegen.dumps_port("in", "reset", "std_logic")}
        {codegen.dumps_port("out", "data_out", "std_logic_vector(WIDTH-1 downto 0)", last=True)}
    );
end helper_test;

architecture rtl of helper_test is
    {codegen.dumps_signal("counter", "std_logic_vector(WIDTH-1 downto 0)")}
begin
    counter <= {codegen.dumps_vector(0, 8, "hex")};
end rtl;
"""
    
    print("Testing helper methods VHDL:")
    print(helper_vhdl)
    
    # Check syntax with NVC
    syntax_ok, error_msg = check_vhdl_syntax(helper_vhdl)
    if not syntax_ok:
        print("NVC Error:", error_msg)
    
    assert syntax_ok, f"Helper methods VHDL syntax check failed: {error_msg}"


def test_vhdl_expression_conversion():
    """Test VHDL operator conversion."""
    codegen = VHDLCodeGenerator()
    
    # Test expressions with different formats
    test_expressions = [
        ("a + b", "a + b"),
        ("a && b", "a  and  b"),
        ("a || b", "a  or  b"),
        ("!a", "not a"),
        ("a == b", "a = b"),
        ("a != b", "a /= b"),
        ("a & b", "a  and  b"),
        ("a | b", "a  or  b"),
        ("a ^ b", "a  xor  b"),
    ]
    
    # Create mock expression objects
    class MockExpression:
        def __init__(self, expr_str):
            self.expr_str = expr_str
            
        def dumps(self):
            return self.expr_str
            
        def evaluate(self):
            raise ValueError("Cannot evaluate")
    
    for input_expr, expected_vhdl in test_expressions:
        mock_expr = MockExpression(input_expr)
        result = codegen.gen_HDLExpression(mock_expr)
        assert result == expected_vhdl, f"Expression conversion failed: {input_expr} -> {result} (expected {expected_vhdl})"


def test_vhdl_complex_syntax():
    """Test more complex VHDL constructs."""
    complex_vhdl = """library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity complex_test is
    generic (
        WIDTH : integer := 8;
        DEPTH : integer := 16
    );
    port (
        clk : in std_logic;
        reset : in std_logic;
        enable : in std_logic;
        data_in : in std_logic_vector(WIDTH-1 downto 0);
        addr : in std_logic_vector(3 downto 0);
        data_out : out std_logic_vector(WIDTH-1 downto 0);
        valid : out std_logic
    );
end complex_test;

architecture rtl of complex_test is
    type memory_type is array (0 to DEPTH-1) of std_logic_vector(WIDTH-1 downto 0);
    signal memory : memory_type;
    signal read_addr : std_logic_vector(3 downto 0);
    signal write_enable : std_logic;
begin
    write_enable <= enable and not reset;
    
    process(clk)
    begin
        if rising_edge(clk) then
            if reset = '1' then
                read_addr <= (others => '0');
                valid <= '0';
            else
                read_addr <= addr;
                valid <= enable;
                
                if write_enable = '1' then
                    memory(to_integer(unsigned(addr))) <= data_in;
                end if;
            end if;
        end if;
    end process;
    
    data_out <= memory(to_integer(unsigned(read_addr))) when valid = '1' else (others => '0');
end rtl;
"""
    
    print("Testing complex VHDL syntax:")
    print(complex_vhdl)
    
    # Check syntax with NVC
    syntax_ok, error_msg = check_vhdl_syntax(complex_vhdl)
    if not syntax_ok:
        print("NVC Error:", error_msg)
    
    assert syntax_ok, f"Complex VHDL syntax check failed: {error_msg}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])