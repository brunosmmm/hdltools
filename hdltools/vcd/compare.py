"""VCD file comparison and equivalence checking."""

import os
import mmap
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional, Iterator, IO
from pathlib import Path
class SimpleVCDParser:
    """Simple standalone VCD parser for comparison purposes."""
    
    def __init__(self):
        self.variables = {}  # id -> variable info
        self.signal_changes = defaultdict(list)  # signal_name -> [(time, value), ...]
        self.current_time = 0
        self.timescale = "1 ns"  # Default timescale
        
    def parse(self, vcd_content: str):
        """Parse VCD content string."""
        lines = vcd_content.split('\n')
        in_dumpvars = False
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
                
            # Parse timescale - can be on same line or next line
            if line.startswith('$timescale'):
                if '$end' in line:
                    # Timescale is on same line: $timescale 1ns $end
                    parts = line.split()
                    if len(parts) >= 2:
                        self.timescale = parts[1]
                else:
                    # Timescale is on next line
                    i += 1
                    if i < len(lines):
                        next_line = lines[i].strip()
                        if next_line and not next_line.startswith('$'):
                            self.timescale = next_line
                i += 1
                continue
            
            # Parse variable declarations
            elif line.startswith('$var'):
                parts = line.split()
                if len(parts) >= 5:
                    var_type = parts[1]
                    size = parts[2]
                    identifier = parts[3]
                    name = parts[4]
                    self.variables[identifier] = {
                        'name': name,
                        'type': var_type, 
                        'width': int(size) if size.isdigit() else 1,
                        'id': identifier
                    }
            
            # Track dumpvars section
            elif line.startswith('$dumpvars'):
                in_dumpvars = True
                
            elif line.startswith('$end') and in_dumpvars:
                in_dumpvars = False
            
            # Parse time changes
            elif line.startswith('#'):
                self.current_time = int(line[1:])
                
            # Parse value changes
            elif len(line) > 1 and line[0] in '01xzXZ':
                value = line[0]
                identifier = line[1:]
                if identifier in self.variables:
                    signal_name = self.variables[identifier]['name']
                    self.signal_changes[signal_name].append((self.current_time, value))
            
            # Parse vector value changes
            elif line.startswith('b') or line.startswith('r'):
                parts = line.split()
                if len(parts) >= 2:
                    value = parts[0][1:]  # Remove 'b' or 'r' prefix
                    identifier = parts[1]
                    if identifier in self.variables:
                        signal_name = self.variables[identifier]['name']
                        self.signal_changes[signal_name].append((self.current_time, value))
            
            i += 1


class VCDComparisonResult:
    """Result of VCD file comparison."""
    
    def __init__(self, equivalent: bool, mismatches: List[str], 
                 detailed_comparison: Dict[str, Any],
                 file1_signals: List[str], file2_signals: List[str]):
        self.equivalent = equivalent
        self.mismatches = mismatches
        self.detailed_comparison = detailed_comparison
        self.file1_signals = file1_signals
        self.file2_signals = file2_signals
    
    def __bool__(self):
        """Return True if files are equivalent."""
        return self.equivalent
    
    def __str__(self):
        """String representation of comparison result."""
        if self.equivalent:
            return f"VCD files are equivalent ({len(self.file1_signals)} signals compared)"
        else:
            return f"VCD files differ ({len(self.mismatches)} mismatches found)"
    
    def print_summary(self, max_mismatches: int = 10):
        """Print a detailed summary of the comparison."""
        print(f"VCD Comparison Summary:")
        print(f"  File 1 signals: {len(self.file1_signals)}")
        print(f"  File 2 signals: {len(self.file2_signals)}")
        print(f"  Equivalent: {self.equivalent}")
        
        if not self.equivalent:
            print(f"\nMismatches found ({len(self.mismatches)}):")
            for i, mismatch in enumerate(self.mismatches[:max_mismatches]):
                print(f"  {i+1}. {mismatch}")
            if len(self.mismatches) > max_mismatches:
                print(f"  ... and {len(self.mismatches) - max_mismatches} more")
            
            print("\nSignal-by-signal comparison:")
            for signal, details in self.detailed_comparison.items():
                status = "✓" if details['matches'] else "✗"
                print(f"  {status} {signal}: File1={details['file1_changes']} File2={details['file2_changes']}")


class VCDStreamingParser:
    """Memory-efficient streaming VCD parser for large files."""
    
    def __init__(self, chunk_size: int = 8192):
        """Initialize streaming parser.
        
        Args:
            chunk_size: Size of chunks to read from file
        """
        self.chunk_size = chunk_size
        self.variables = {}
        self.current_time = 0
        
    def parse_file_streaming(self, vcd_path: str) -> Iterator[Tuple[str, int, str]]:
        """Parse VCD file in streaming fashion yielding (signal_name, time, value) tuples.
        
        Args:
            vcd_path: Path to VCD file
            
        Yields:
            Tuples of (signal_name, time, value) for each signal change
        """
        with open(vcd_path, 'rb') as f:
            # Try to use memory mapping for large files
            try:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    yield from self._parse_mmap(mm)
            except (OSError, ValueError):
                # Fall back to regular file reading if mmap fails
                f.seek(0)
                yield from self._parse_file_chunks(f)
    
    def _parse_mmap(self, mm: mmap.mmap) -> Iterator[Tuple[str, int, str]]:
        """Parse memory-mapped VCD file."""
        buffer = b''
        mm.seek(0)
        
        while True:
            chunk = mm.read(self.chunk_size)
            if not chunk:
                break
                
            buffer += chunk
            
            # Process complete lines
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                yield from self._process_line(line.decode('utf-8', errors='ignore'))
        
        # Process any remaining buffer
        if buffer:
            yield from self._process_line(buffer.decode('utf-8', errors='ignore'))
    
    def _parse_file_chunks(self, f: IO[bytes]) -> Iterator[Tuple[str, int, str]]:
        """Parse file using chunk-based reading."""
        buffer = b''
        
        while True:
            chunk = f.read(self.chunk_size)
            if not chunk:
                break
                
            buffer += chunk
            
            # Process complete lines
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                yield from self._process_line(line.decode('utf-8', errors='ignore'))
        
        # Process any remaining buffer
        if buffer:
            yield from self._process_line(buffer.decode('utf-8', errors='ignore'))
    
    def _process_line(self, line: str) -> Iterator[Tuple[str, int, str]]:
        """Process a single VCD line and yield signal changes."""
        line = line.strip()
        if not line:
            return
        
        # Parse variable declarations
        if line.startswith('$var'):
            parts = line.split()
            if len(parts) >= 5:
                var_type = parts[1]
                size = parts[2]
                identifier = parts[3]
                name = parts[4]
                self.variables[identifier] = {
                    'name': name, 
                    'size': size, 
                    'type': var_type
                }
        
        # Parse time changes
        elif line.startswith('#'):
            self.current_time = int(line[1:])
        
        # Parse value changes
        elif len(line) > 1 and line[0] in '01xzXZ':
            value = line[0]
            identifier = line[1:]
            if identifier in self.variables:
                signal_name = self.variables[identifier]['name']
                yield (signal_name, self.current_time, value)
        
        # Parse vector value changes
        elif line.startswith('b') or line.startswith('r'):
            parts = line.split()
            if len(parts) >= 2:
                value = parts[0][1:]  # Remove 'b' or 'r' prefix
                identifier = parts[1]
                if identifier in self.variables:
                    signal_name = self.variables[identifier]['name']
                    yield (signal_name, self.current_time, value)


class VCDStreamingComparator:
    """Memory-efficient VCD comparator for large files."""
    
    def __init__(self, time_tolerance: float = 1e-9, max_memory_mb: int = 100):
        """Initialize streaming comparator.
        
        Args:
            time_tolerance: Maximum time difference to consider equivalent
            max_memory_mb: Maximum memory to use for buffering (MB)
        """
        self.time_tolerance = time_tolerance
        self.max_memory_mb = max_memory_mb
        self.max_buffer_size = max_memory_mb * 1024 * 1024 // 16  # Rough estimate
    
    def compare_files_streaming(self, vcd_file1: str, vcd_file2: str) -> VCDComparisonResult:
        """Compare two VCD files using streaming for memory efficiency.
        
        Args:
            vcd_file1: Path to first VCD file
            vcd_file2: Path to second VCD file
            
        Returns:
            VCDComparisonResult containing detailed comparison information
        """
        # Get file sizes to determine if streaming is beneficial
        size1 = os.path.getsize(vcd_file1)
        size2 = os.path.getsize(vcd_file2)
        total_size_mb = (size1 + size2) / (1024 * 1024)
        
        if total_size_mb > self.max_memory_mb:
            # Use streaming approach for large files
            return self._compare_streaming(vcd_file1, vcd_file2)
        else:
            # Fall back to regular comparison for smaller files
            regular_comparator = VCDComparator(self.time_tolerance)
            return regular_comparator.compare_files(vcd_file1, vcd_file2)
    
    def _compare_streaming(self, vcd_file1: str, vcd_file2: str) -> VCDComparisonResult:
        """Perform streaming comparison of two large VCD files."""
        parser1 = VCDStreamingParser()
        parser2 = VCDStreamingParser()
        
        # Get iterators for both files
        changes1_iter = parser1.parse_file_streaming(vcd_file1)
        changes2_iter = parser2.parse_file_streaming(vcd_file2)
        
        # Buffer changes for comparison
        buffer1 = defaultdict(list)
        buffer2 = defaultdict(list)
        
        mismatches = []
        detailed_comparison = defaultdict(lambda: {
            'file1_changes': 0,
            'file2_changes': 0, 
            'matches': True
        })
        
        all_signals = set()
        
        # Process changes in chunks to manage memory
        try:
            # Collect all changes from both files
            for signal, time, value in changes1_iter:
                buffer1[signal].append((time, value))
                all_signals.add(signal)
                detailed_comparison[signal]['file1_changes'] += 1
                
                # Flush buffer if getting too large
                if len(buffer1) * len(buffer1.get(signal, [])) > self.max_buffer_size:
                    self._process_buffer_chunk(buffer1, buffer2, mismatches, detailed_comparison)
            
            for signal, time, value in changes2_iter:
                buffer2[signal].append((time, value))
                all_signals.add(signal)
                detailed_comparison[signal]['file2_changes'] += 1
                
                # Flush buffer if getting too large
                if len(buffer2) * len(buffer2.get(signal, [])) > self.max_buffer_size:
                    self._process_buffer_chunk(buffer1, buffer2, mismatches, detailed_comparison)
            
            # Process remaining buffered changes
            self._process_buffer_chunk(buffer1, buffer2, mismatches, detailed_comparison)
            
        except Exception as e:
            mismatches.append(f"Streaming comparison failed: {str(e)}")
        
        return VCDComparisonResult(
            equivalent=len(mismatches) == 0,
            mismatches=mismatches,
            detailed_comparison=dict(detailed_comparison),
            file1_signals=list(buffer1.keys()),
            file2_signals=list(buffer2.keys())
        )
    
    def _process_buffer_chunk(self, buffer1: Dict, buffer2: Dict, 
                            mismatches: List[str], detailed_comparison: Dict):
        """Process a chunk of buffered changes."""
        common_signals = set(buffer1.keys()) & set(buffer2.keys())
        
        for signal in common_signals:
            changes1 = sorted(buffer1[signal], key=lambda x: x[0])
            changes2 = sorted(buffer2[signal], key=lambda x: x[0])
            
            # Compare changes for this signal
            if len(changes1) != len(changes2):
                detailed_comparison[signal]['matches'] = False
                mismatches.append(f"Signal '{signal}': different number of changes "
                                f"(File1: {len(changes1)}, File2: {len(changes2)})")
                continue
            
            for i, ((time1, val1), (time2, val2)) in enumerate(zip(changes1, changes2)):
                if abs(time1 - time2) > self.time_tolerance:
                    detailed_comparison[signal]['matches'] = False
                    mismatches.append(f"Signal '{signal}' change {i}: time mismatch "
                                    f"(File1: {time1}, File2: {time2})")
                
                val1_norm = self._normalize_value(val1)
                val2_norm = self._normalize_value(val2)
                
                if val1_norm != val2_norm:
                    detailed_comparison[signal]['matches'] = False
                    mismatches.append(f"Signal '{signal}' at time {time1}: value mismatch "
                                    f"(File1: '{val1}', File2: '{val2}')")
        
        # Clear processed signals from buffers
        for signal in common_signals:
            if signal in buffer1:
                del buffer1[signal]
            if signal in buffer2:
                del buffer2[signal]
    
    def _normalize_value(self, value: str) -> str:
        """Normalize signal values for comparison."""
        if isinstance(value, str):
            value = value.lower()
            if value in ['x', 'z', 'u', '-']:
                return 'x'
            return value.strip()
        return str(value)


class VCDComparator:
    """Compare VCD files for functional equivalence."""
    
    def __init__(self, time_tolerance: float = 1e-9):
        """Initialize VCD comparator.
        
        Args:
            time_tolerance: Maximum time difference to consider equivalent (in simulation time units)
        """
        self.time_tolerance = time_tolerance
    
    def parse_vcd_file(self, vcd_path: str) -> Tuple[Dict[str, List[Tuple[int, str]]], str]:
        """Parse a VCD file and extract signal changes with timescale.
        
        Args:
            vcd_path: Path to VCD file
            
        Returns:
            Tuple of (signal_changes_dict, timescale_string)
        """
        with open(vcd_path, 'r') as f:
            vcd_content = f.read()
        
        parser = SimpleVCDParser()
        parser.parse(vcd_content)
        return dict(parser.signal_changes), parser.timescale
    
    def _simple_parse_vcd(self, vcd_path: str) -> Dict[str, List[Tuple[int, str]]]:
        """Fallback simple VCD parsing when main parser fails."""
        changes = defaultdict(list)
        
        with open(vcd_path, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        signals = {}
        current_time = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse variable declarations
            if line.startswith('$var'):
                parts = line.split()
                if len(parts) >= 5:
                    var_type = parts[1]
                    size = parts[2] 
                    identifier = parts[3]
                    name = parts[4]
                    signals[identifier] = {'name': name, 'size': size, 'type': var_type}
            
            # Parse time changes
            elif line.startswith('#'):
                current_time = int(line[1:])
                
            # Parse value changes
            elif len(line) > 1 and line[0] in '01xzXZ':
                value = line[0]
                identifier = line[1:]
                if identifier in signals:
                    signal_name = signals[identifier]['name']
                    changes[signal_name].append((current_time, value))
            
            # Parse vector value changes
            elif line.startswith('b') or line.startswith('r'):
                parts = line.split()
                if len(parts) >= 2:
                    value = parts[0][1:]  # Remove 'b' or 'r' prefix
                    identifier = parts[1]
                    if identifier in signals:
                        signal_name = signals[identifier]['name']
                        changes[signal_name].append((current_time, value))
        
        return dict(changes)
    
    def normalize_time(self, time_value: int, timescale: str) -> int:
        """Normalize time values to nanoseconds for cross-language comparison.
        
        Args:
            time_value: Time value from VCD file
            timescale: Timescale string (e.g., "1 fs", "1 ns")
            
        Returns:
            Time value normalized to nanoseconds
        """
        if "fs" in timescale:
            return time_value // 1_000_000  # Convert femtoseconds to nanoseconds
        elif "ps" in timescale:
            return time_value // 1_000      # Convert picoseconds to nanoseconds
        elif "ns" in timescale:
            return time_value               # Already in nanoseconds
        elif "us" in timescale:
            return time_value * 1_000       # Convert microseconds to nanoseconds
        else:
            # Default assumption: treat as nanoseconds
            return time_value
    
    def normalize_value(self, value: str) -> str:
        """Normalize signal values for comparison.
        
        Args:
            value: Signal value to normalize
            
        Returns:
            Normalized value string
        """
        if isinstance(value, str):
            # Handle different representations of unknown/high-impedance
            value_lower = value.lower()
            
            # Handle VHDL undefined values - convert UUUU to x
            if all(c.upper() in 'UXZ-' for c in value):
                return 'x'  # Normalize all unknown states to single x
            
            # For binary values, normalize by removing leading zeros to compare bit patterns
            if len(value) > 1 and all(c in '01' for c in value):
                # Remove leading zeros for comparison (e.g., "0011" -> "11", "0000" -> "0")
                normalized = value_lower.lstrip('0')
                if not normalized:  # All zeros case
                    return '0'
                return normalized
            
            # Single bit values
            if value_lower in ['x', 'z', 'u', '-']:
                return 'x'  # Normalize all unknown states
            
            # Handle binary values with leading/trailing whitespace
            return value_lower.strip()
        return str(value)
    
    def normalize_signal_name(self, signal_name: str) -> str:
        """Normalize signal names to handle differences between Verilog and VHDL.
        
        Args:
            signal_name: Original signal name
            
        Returns:
            Normalized signal name
        """
        # Remove array notation from VHDL signals: count[3:0] -> count
        if '[' in signal_name and ']' in signal_name:
            return signal_name.split('[')[0]
        return signal_name
    
    def compare_signal_changes(self, changes1: Dict[str, List[Tuple[int, str]]], 
                             changes2: Dict[str, List[Tuple[int, str]]],
                             timescale1: str = "1 ns", timescale2: str = "1 ns") -> Tuple[List[str], Dict[str, Any]]:
        """Compare signal changes between two VCD files.
        
        Args:
            changes1: Signal changes from first file
            changes2: Signal changes from second file
            timescale1: Timescale of first file
            timescale2: Timescale of second file
            
        Returns:
            Tuple of (mismatches, detailed_comparison)
        """
        # Normalize signal names and times to handle Verilog vs VHDL differences
        normalized_changes1 = {}
        normalized_changes2 = {}
        
        for signal, changes in changes1.items():
            norm_signal = self.normalize_signal_name(signal)
            # Normalize times for this file
            norm_changes = [(self.normalize_time(time, timescale1), value) for time, value in changes]
            if norm_signal in normalized_changes1:
                # Merge changes if multiple signals map to same normalized name
                normalized_changes1[norm_signal].extend(norm_changes)
            else:
                normalized_changes1[norm_signal] = norm_changes
        
        for signal, changes in changes2.items():
            norm_signal = self.normalize_signal_name(signal)
            # Normalize times for this file  
            norm_changes = [(self.normalize_time(time, timescale2), value) for time, value in changes]
            if norm_signal in normalized_changes2:
                normalized_changes2[norm_signal].extend(norm_changes)
            else:
                normalized_changes2[norm_signal] = norm_changes
        
        # Get all normalized signal names
        all_signals = set(normalized_changes1.keys()) | set(normalized_changes2.keys())
        
        mismatches = []
        detailed_comparison = {}
        
        for signal in all_signals:
            changes_1 = normalized_changes1.get(signal, [])
            changes_2 = normalized_changes2.get(signal, [])
            
            # Store detailed comparison info
            detailed_comparison[signal] = {
                'file1_changes': len(changes_1),
                'file2_changes': len(changes_2),
                'matches': True
            }
            
            if len(changes_1) != len(changes_2):
                detailed_comparison[signal]['matches'] = False
                mismatches.append(f"Signal '{signal}': different number of changes "
                                f"(File1: {len(changes_1)}, File2: {len(changes_2)})")
                continue
            
            # Sort changes by time to ensure proper comparison
            changes_1_sorted = sorted(changes_1, key=lambda x: x[0])
            changes_2_sorted = sorted(changes_2, key=lambda x: x[0])
            
            # Compare each change
            for i, ((time1, val1), (time2, val2)) in enumerate(zip(changes_1_sorted, changes_2_sorted)):
                # Normalize values for comparison
                val1_norm = self.normalize_value(val1)
                val2_norm = self.normalize_value(val2)
                
                if abs(time1 - time2) > self.time_tolerance:
                    detailed_comparison[signal]['matches'] = False
                    mismatches.append(f"Signal '{signal}' change {i}: time mismatch "
                                    f"(File1: {time1}, File2: {time2})")
                
                if val1_norm != val2_norm:
                    detailed_comparison[signal]['matches'] = False
                    mismatches.append(f"Signal '{signal}' at time {time1}: value mismatch "
                                    f"(File1: '{val1}' -> '{val1_norm}', File2: '{val2}' -> '{val2_norm}')")
        
        return mismatches, detailed_comparison
    
    def compare_files(self, vcd_file1: str, vcd_file2: str) -> VCDComparisonResult:
        """Compare two VCD files for functional equivalence.
        
        Args:
            vcd_file1: Path to first VCD file
            vcd_file2: Path to second VCD file
            
        Returns:
            VCDComparisonResult containing detailed comparison information
        """
        changes1, timescale1 = self.parse_vcd_file(vcd_file1)
        changes2, timescale2 = self.parse_vcd_file(vcd_file2)
        
        mismatches, detailed_comparison = self.compare_signal_changes(changes1, changes2, timescale1, timescale2)
        
        return VCDComparisonResult(
            equivalent=len(mismatches) == 0,
            mismatches=mismatches,
            detailed_comparison=detailed_comparison,
            file1_signals=list(changes1.keys()),
            file2_signals=list(changes2.keys())
        )


def compare_vcd_files(vcd_file1: str, vcd_file2: str, time_tolerance: float = 1e-9, 
                     use_streaming: bool = None, max_memory_mb: int = 100) -> VCDComparisonResult:
    """Convenience function to compare two VCD files.
    
    Args:
        vcd_file1: Path to first VCD file
        vcd_file2: Path to second VCD file  
        time_tolerance: Maximum time difference to consider equivalent
        use_streaming: Force streaming mode (True/False) or auto-detect (None)
        max_memory_mb: Maximum memory to use for buffering in streaming mode
        
    Returns:
        VCDComparisonResult containing detailed comparison information
        
    Example:
        >>> result = compare_vcd_files("simulation1.vcd", "simulation2.vcd")
        >>> if result:
        ...     print("Files are equivalent")
        >>> else:
        ...     result.print_summary()
        
        >>> # Force streaming for large files
        >>> result = compare_vcd_files("large1.vcd", "large2.vcd", use_streaming=True)
    """
    if use_streaming is True:
        # Force streaming mode
        comparator = VCDStreamingComparator(time_tolerance=time_tolerance, max_memory_mb=max_memory_mb)
        return comparator.compare_files_streaming(vcd_file1, vcd_file2)
    elif use_streaming is False:
        # Force regular mode
        comparator = VCDComparator(time_tolerance=time_tolerance)
        return comparator.compare_files(vcd_file1, vcd_file2)
    else:
        # Auto-detect based on file size
        size1 = os.path.getsize(vcd_file1) if os.path.exists(vcd_file1) else 0
        size2 = os.path.getsize(vcd_file2) if os.path.exists(vcd_file2) else 0
        total_size_mb = (size1 + size2) / (1024 * 1024)
        
        if total_size_mb > max_memory_mb:
            comparator = VCDStreamingComparator(time_tolerance=time_tolerance, max_memory_mb=max_memory_mb)
            return comparator.compare_files_streaming(vcd_file1, vcd_file2)
        else:
            comparator = VCDComparator(time_tolerance=time_tolerance)
            return comparator.compare_files(vcd_file1, vcd_file2)