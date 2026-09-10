"""VCD to FST converter implementation."""

from typing import Optional, Dict, List, Set
from pathlib import Path
import re

from hdltools.vcd.streaming_parser import StreamingVCDParser
from hdltools.vcd.mixins.hierarchy import VCDHierarchyAnalysisMixin
from hdltools.vcd.variable import VCDVariable

from .generator import FSTStreamingGenerator
from . import FSTError


class VCD2FSTConverter(StreamingVCDParser, VCDHierarchyAnalysisMixin):
    """Convert VCD files to FST format.
    
    Provides efficient streaming conversion from VCD to FST format
    with minimal memory usage.
    """
    
    def __init__(self, vcd_file: str, fst_file: str,
                 compress_level: int = 6,
                 filter_signals: Optional[List[str]] = None):
        """Initialize converter.
        
        Args:
            vcd_file: Input VCD filename
            fst_file: Output FST filename
            compress_level: FST compression level (0-9)
            filter_signals: Optional list of signal patterns to include
        """
        super().__init__()
        self.vcd_file = Path(vcd_file)
        self.fst_file = Path(fst_file)
        self.compress_level = compress_level
        self.filter_patterns = [re.compile(p) for p in (filter_signals or [])]
        
        # FST generator
        self._fst_gen: Optional[FSTStreamingGenerator] = None
        
        # Conversion state
        self._var_map: Dict[str, str] = {}  # VCD ID -> FST ID mapping
        self._filtered_vars: Set[str] = set()
        self._current_time = 0
        self._pending_changes: List[tuple[str, str]] = []
        self._variables_written = False
        
    def convert(self):
        """Perform VCD to FST conversion."""
        print(f"Converting {self.vcd_file} to {self.fst_file}")

        with FSTStreamingGenerator(
            str(self.fst_file),
            self.timescale or "1ns",
            self.compress_level,
        ) as self._fst_gen:
            self.parse(str(self.vcd_file))
            # Header-only VCDs never hit value handlers — still emit hierarchy.
            self._write_variables()
            if self._pending_changes and self._variables_written:
                self._fst_gen.write_time_block(
                    self._current_time, self._pending_changes
                )
                self._pending_changes = []

        if not self._var_map:
            raise FSTError(
                "VCD→FST conversion wrote no variables "
                f"(input={self.vcd_file})"
            )

        print(f"Conversion complete. Output: {self.fst_file}")
        print(f"  Variables: {len(self._var_map)}")
        print(f"  Compression: {self.compress_level}")
        
    def header_statement_handler(self, stmt, fields):
        """Handle VCD header statements."""
        # Process timescale
        if hasattr(stmt, 'name') and stmt.name == 'TIMESCALE_PARSER':
            if 'timescale' in fields:
                # Extract timescale value
                ts_match = re.match(r'(\d+)(\w+)', fields['timescale'])
                if ts_match:
                    self.timescale = fields['timescale']
                    
    def _should_include_variable(self, var: VCDVariable) -> bool:
        """Check if variable should be included based on filters."""
        if not self.filter_patterns:
            return True

        scope_path = self._variable_scope_path(var)
        full_name = ".".join(scope_path + [var.name or ""])
        return any(p.search(full_name) for p in self.filter_patterns)
        
    @staticmethod
    def _variable_scope_path(var: VCDVariable) -> List[str]:
        """Build FST scope path from a VCDVariable (hierarchy mixin has no .reference)."""
        ref = getattr(var, "reference", None)
        if ref:
            parts = ref.split(".")
            return parts[:-1] if len(parts) > 1 else ["top"]
        if var.scope is not None and len(var.scope) > 0:
            return [var.scope[i] for i in range(len(var.scope))]
        return ["top"]

    def _write_variables(self):
        """Write variable definitions to FST."""
        if self._variables_written:
            return
        if self._fst_gen is None:
            return

        # Prefer hierarchy mixin map; fall back to streaming parser storage.
        variables = self.variables or getattr(self, "_variables", {})

        var_type_map = {
            "wire": "wire",
            "reg": "reg",
            "integer": "integer",
            "real": "real",
            "event": "wire",
            "parameter": "wire",
        }

        var_count = 0
        for vcd_id, var in variables.items():
            if not self._should_include_variable(var):
                self._filtered_vars.add(vcd_id)
                continue

            # VCDVariable API: var_type / size / name / scope (not type/width/reference)
            fst_type = var_type_map.get(var.var_type, "wire")
            scope_path = self._variable_scope_path(var)
            var_name = var.name or vcd_id
            width = var.size if var.size is not None else 1

            self._fst_gen.add_variable(
                var_id=vcd_id,
                name=var_name,
                var_type=fst_type,
                width=width,
                scope_path=scope_path,
            )
            self._var_map[vcd_id] = vcd_id
            var_count += 1

        self._fst_gen.write_header()
        self._variables_written = True
        print(f"  Wrote {var_count} variables (filtered {len(self._filtered_vars)})")

    def _state_change_handler(self, old_state, new_state):
        """Write FST hierarchy as soon as the VCD header completes."""
        super()._state_change_handler(old_state, new_state)
        if old_state == "header" and new_state in ("initial", "dump"):
            self._write_variables()

    def initial_value_handler(self, stmt, fields):
        """Handle initial value assignments."""
        self._write_variables()

        var_id = fields.get("var")
        value = fields.get("value")
        # Do not use truthiness on value: "0" is a real VCD value.
        if var_id is not None and value is not None and var_id not in self._filtered_vars:
            self._pending_changes.append((var_id, value))

    def value_change_handler(self, stmt, fields):
        """Handle value changes."""
        self._write_variables()

        var_id = fields.get("var")
        value = fields.get("value")
        if var_id is not None and value is not None and var_id not in self._filtered_vars:
            self._pending_changes.append((var_id, value))

    def clock_change_handler(self, time):
        """Handle time changes."""
        self._write_variables()
        if self._pending_changes and self._variables_written:
            self._fst_gen.write_time_block(self._current_time, self._pending_changes)
            self._pending_changes = []

        self._current_time = time
        

class FST2VCDConverter:
    """Convert FST files back to VCD format.
    
    Useful for compatibility with tools that only support VCD.
    """
    
    def __init__(self, fst_file: str, vcd_file: str):
        """Initialize converter.
        
        Args:
            fst_file: Input FST filename
            vcd_file: Output VCD filename
        """
        self.fst_file = Path(fst_file)
        self.vcd_file = Path(vcd_file)
        
    def convert(self):
        """Perform FST to VCD conversion."""
        # This would be implemented using FSTParser
        # For now, raise not implemented
        raise NotImplementedError("FST to VCD conversion not yet implemented")
        

def convert_vcd_to_fst(vcd_file: str, fst_file: str,
                      compress_level: int = 6,
                      filter_signals: Optional[List[str]] = None) -> None:
    """Convenience function to convert VCD to FST.
    
    Args:
        vcd_file: Input VCD file
        fst_file: Output FST file
        compress_level: Compression level (0-9)
        filter_signals: Optional signal filters
    """
    converter = VCD2FSTConverter(vcd_file, fst_file, compress_level, filter_signals)
    converter.convert()
    

def convert_fst_to_vcd(fst_file: str, vcd_file: str) -> None:
    """Convenience function to convert FST to VCD.
    
    Args:
        fst_file: Input FST file
        vcd_file: Output VCD file
    """
    converter = FST2VCDConverter(fst_file, vcd_file)
    converter.convert()