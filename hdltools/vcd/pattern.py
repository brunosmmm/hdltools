"""VCD pattern matcher."""

from typing import Dict
from hdltools.patterns.matcher import PatternMatcher
from hdltools.vcd.streaming_parser import StreamingVCDParser
from hdltools.vcd.parser import VAR_PARSER
from hdltools.vcd.variable import VCDVariable
try:
    from hdltools.vcd.efficient_storage import BinarySignalValue
    _EFFICIENT_AVAILABLE = True
except ImportError:
    _EFFICIENT_AVAILABLE = False


# TODO: extract pattern matching logic and abstract to generic data source
class VCDPatternMatcher(StreamingVCDParser):
    """VCD pattern matcher."""

    def __init__(
        self,
        oneshot_patterns: bool = True,
        **watchlist: Dict[str, PatternMatcher]
    ):
        """Initialize.

        Arguments
        ---------
        watchlist
          A variable name to pattern mapping list
        oneshot_patterns
          Whether to match a pattern multiple times or not
        """
        super().__init__()
        for pattern in watchlist.values():
            if not isinstance(pattern, PatternMatcher):
                raise TypeError(
                    "values of watchlist mapping must be PatternMatcher objects"
                )
            # set default callback
            if pattern.match_cb is None:
                pattern.match_cb = self._match_callback
        # store watchlist
        self._match_map = watchlist
        # internal variable mapping
        self._var_map = {}
        self._oneshot = oneshot_patterns

    def header_statement_handler(self, stmt, fields):
        """Handle header statements with efficient variable creation."""
        if stmt == VAR_PARSER:
            # build variable mapping with efficient lookup support
            if fields["name"] in self._match_map:
                var = VCDVariable(
                    fields["id"],
                    var_type=fields["vtype"],
                    size=fields["width"],
                    name=fields["name"],
                )
                self._var_map[fields["id"]] = var
                
                # Pre-create binary value templates if efficient storage available
                if _EFFICIENT_AVAILABLE and hasattr(self, '_use_efficient') and self._use_efficient:
                    # Create a template for efficient binary operations
                    width = fields.get("width", 1)
                    self._binary_templates = getattr(self, '_binary_templates', {})
                    self._binary_templates[fields["id"]] = BinarySignalValue(width)

    def initial_value_handler(self, stmt, fields):
        """Handle initial value assignments."""
        if fields["var"] in self._var_map:
            self._match_map[
                self._var_map[fields["var"]].name
            ].initial = fields["value"]

    def value_change_handler(self, stmt, fields):
        """Handle value changes with optimized lookups."""
        var_id = fields["var"]
        if var_id in self._var_map:
            # Optimized variable access
            vcd_var = self._var_map[var_id]
            pattern_matcher = self._match_map[vcd_var.name]
            
            value = fields["value"]
            
            # Use efficient binary operations if available
            if _EFFICIENT_AVAILABLE and hasattr(self, '_binary_templates') and var_id in self._binary_templates:
                # Convert to binary for potential efficiency gains in pattern matching
                binary_template = self._binary_templates[var_id]
                try:
                    binary_template.set_value(value)
                    # For now, still use string value for pattern matching compatibility
                    # Future: extend PatternMatcher to support binary operations
                    processed_value = value
                except (ValueError, TypeError, OverflowError):
                    # Fall back to string if binary conversion fails
                    processed_value = value
            else:
                processed_value = value
            
            # try to match with processed value
            if not self._oneshot or (self._oneshot and not pattern_matcher.finished):
                pattern_matcher.new_state(processed_value)
                if pattern_matcher.finished and not self._oneshot:
                    pattern_matcher.restart()

    def _match_callback(self, matcher_obj):
        """Match callback."""
        pass
    
    # Efficient query methods for pattern analysis
    def get_active_patterns(self):
        """Get currently active (unfinished) patterns."""
        return {name: matcher for name, matcher in self._match_map.items() 
                if not matcher.finished}
    
    def get_completed_patterns(self):
        """Get completed patterns."""
        return {name: matcher for name, matcher in self._match_map.items() 
                if matcher.finished}
    
    def get_pattern_statistics(self):
        """Get pattern matching statistics."""
        stats = {
            'total_patterns': len(self._match_map),
            'active_patterns': len(self.get_active_patterns()),
            'completed_patterns': len(self.get_completed_patterns()),
            'variables_watched': len(self._var_map)
        }
        
        # Add per-pattern statistics
        stats['pattern_details'] = {}
        for name, matcher in self._match_map.items():
            stats['pattern_details'][name] = {
                'finished': matcher.finished,
                'current_state': getattr(matcher, 'current_state', None),
                'match_count': getattr(matcher, 'match_count', 0)
            }
        
        return stats
    
    def reset_patterns(self):
        """Reset all patterns to initial state."""
        for matcher in self._match_map.values():
            matcher.restart()
    
    def get_pattern_efficiency_info(self):
        """Get information about pattern matching efficiency."""
        info = {
            'efficient_storage_available': _EFFICIENT_AVAILABLE,
            'efficient_storage_enabled': hasattr(self, '_use_efficient') and self._use_efficient,
            'binary_templates_created': hasattr(self, '_binary_templates') and len(getattr(self, '_binary_templates', {}))
        }
        return info
