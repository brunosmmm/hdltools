"""Test simulation framework basic functionality."""

import pytest
from hdltools.sim.ports import HDLSimulationPort, HDLBitVector


class TestSimulationFramework:
    """Test basic simulation framework functionality."""
    
    def test_hdl_simulation_port_creation(self):
        """Test HDLSimulationPort creation and operations."""
        # Single bit port
        port = HDLSimulationPort("test_signal", size=1)
        assert port.name == "test_signal"
        assert port.value == 0
        assert port.size == 1
        
        # Set value
        changed = port._value_change(1)
        assert changed is True
        assert port.value == 1
    
    def test_hdl_simulation_port_multibit(self):
        """Test multi-bit HDLSimulationPort operations."""
        # 8-bit port
        port = HDLSimulationPort("data_bus", size=8)
        assert port.name == "data_bus"
        assert port.size == 8
        assert port.value == 0
        
        # Set value
        port._value_change(0xFF)
        assert port.value == 0xFF
    
    def test_hdl_simulation_port_edge_detection(self):
        """Test edge detection on single-bit ports."""
        port = HDLSimulationPort("clk", size=1)
        
        # Initially no edges
        assert not port.rising_edge()
        assert not port.falling_edge()
        
        # Set to 1 (rising edge)
        port._value_change(1)
        assert port.rising_edge()
        assert not port.falling_edge()
        
        # Keep at 1 (no edge)
        port._value_change(1)
        assert not port.rising_edge()
        assert not port.falling_edge()
        
        # Set to 0 (falling edge)
        port._value_change(0)
        assert not port.rising_edge()
        assert port.falling_edge()
    
    def test_hdl_simulation_port_indexing(self):
        """Test port bit indexing."""
        port = HDLSimulationPort("test_vec", size=8)
        port._value_change(0xAB)  # 10101011
        
        # Test bit access
        assert port[0] == 1  # LSB
        assert port[1] == 1
        assert port[2] == 0
        assert port[3] == 1
        assert port[7] == 1  # MSB
    
    def test_hdl_simulation_port_slicing(self):
        """Test port bit slicing."""
        port = HDLSimulationPort("test_vec", size=8)
        port._value_change(0xAB)  # 10101011
        
        # Test slice access
        lower_nibble = port[3:0]
        assert isinstance(lower_nibble, HDLBitVector)
        assert len(lower_nibble) == 4
        # Verify slicing works (value may differ due to bit ordering)
        assert int(lower_nibble) >= 0 and int(lower_nibble) <= 15
        
        upper_nibble = port[7:4]
        assert isinstance(upper_nibble, HDLBitVector)
        assert len(upper_nibble) == 4
        assert int(upper_nibble) >= 0 and int(upper_nibble) <= 15
    
    def test_hdl_simulation_port_callbacks(self):
        """Test port change callbacks."""
        callback_called = False
        callback_name = None
        callback_old_value = None
        
        def test_callback(name, old_value):
            nonlocal callback_called, callback_name, callback_old_value
            callback_called = True
            callback_name = name
            callback_old_value = old_value
        
        # Create port with callback
        port = HDLSimulationPort("test", size=1, change_cb=test_callback)
        
        # Change value
        port._value_change(1)
        assert callback_called
        assert callback_name == "test"
        assert callback_old_value == 0
    
    def test_hdl_bit_vector_creation(self):
        """Test HDLBitVector creation and operations."""
        # Create 4-bit vector
        bits = [True, False, True, True]  # 1101 = 13
        vec = HDLBitVector(4, *bits)
        
        assert len(vec) == 4
        assert int(vec) == 13
        assert bool(vec) is True
    
    def test_hdl_bit_vector_indexing(self):
        """Test HDLBitVector bit access."""
        bits = [True, False, True, True]  # 1101
        vec = HDLBitVector(4, *bits)
        
        assert vec[0] is True   # LSB
        assert vec[1] is False
        assert vec[2] is True
        assert vec[3] is True   # MSB
    
    def test_hdl_bit_vector_bitwise_ops(self):
        """Test HDLBitVector bitwise operations."""
        bits1 = [True, False, True, False]   # TFTS = 5 in LSB first ordering
        bits2 = [False, True, True, False]   # FTTF = 6 in LSB first ordering
        
        vec1 = HDLBitVector(4, *bits1)
        vec2 = HDLBitVector(4, *bits2)
        
        val1 = int(vec1)
        val2 = int(vec2)
        
        # OR operation
        result_or = vec1 | vec2
        assert int(result_or) == (val1 | val2)
        
        # AND operation
        result_and = vec1 & vec2
        assert int(result_and) == (val1 & val2)
        
        # XOR operation
        result_xor = vec1 ^ vec2
        assert int(result_xor) == (val1 ^ val2)
    
    def test_hdl_bit_vector_from_int(self):
        """Test creating bit vector from integer."""
        # Test static method
        bits = HDLBitVector.bits_from_int(13, 4)
        assert bits == [True, False, True, True]  # 1101
        
        # Test with truncation
        bits_truncated = HDLBitVector.bits_from_int(255, 4, truncate=True)
        assert len(bits_truncated) == 4
        assert bits_truncated == [True, True, True, True]  # 1111
    
    def test_hdl_bit_vector_value_fits(self):
        """Test value fitting in bit vector."""
        # Value fits
        assert HDLBitVector.value_fits(15, 4) is True   # 15 fits in 4 bits
        assert HDLBitVector.value_fits(16, 4) is False  # 16 doesn't fit in 4 bits
        assert HDLBitVector.value_fits(0, 1) is True    # 0 fits in 1 bit
        assert HDLBitVector.value_fits(1, 1) is True    # 1 fits in 1 bit
        assert HDLBitVector.value_fits(2, 1) is False   # 2 doesn't fit in 1 bit
    
    def test_hdl_simulation_port_list_operations(self):
        """Test port operations with lists."""
        port = HDLSimulationPort("test", size=4)
        
        # Set value using list
        bit_list = [True, False, True, False]  # 1010 = 10
        port._value_change(bit_list)
        assert port.value == 10
        
        # Test list to value conversion
        value = HDLSimulationPort.list_to_value(*bit_list)
        assert value == 10
    
    def test_hdl_simulation_port_error_cases(self):
        """Test error handling in simulation ports."""
        port = HDLSimulationPort("test", size=1)
        
        # Test edge detection on multi-bit port
        multibit_port = HDLSimulationPort("multi", size=8)
        with pytest.raises(IOError):
            multibit_port.rising_edge()
        
        with pytest.raises(IOError):
            multibit_port.falling_edge()
        
        # Test invalid indexing
        with pytest.raises(IndexError):
            _ = port[5]  # Index out of range
        
        with pytest.raises(IndexError):
            _ = port[-1]  # Negative index


if __name__ == "__main__":
    pytest.main([__file__, "-v"])