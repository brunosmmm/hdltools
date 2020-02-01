"""VCD pattern matcher."""

from typing import Dict
from hdltools.patterns.matcher import PatternMatcher
from hdltools.vcd.parser import BaseVCDParser, VAR_PARSER
from hdltools.vcd import VCDVariable


class VCDPatternMatcher(BaseVCDParser):
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
        """Handle header statements."""
        if stmt == VAR_PARSER:
            # build variable mapping
            if fields["name"] in self._match_map:
                var = VCDVariable(
                    fields["id"],
                    var_type=fields["vtype"],
                    size=fields["width"],
                    name=fields["name"],
                )
                self._var_map[fields["id"]] = var

    def initial_value_handler(self, stmt, fields):
        """Handle initial value assignments."""
        if fields["var"] in self._var_map:
            self._match_map[
                self._var_map[fields["var"]].name
            ].initial = fields["value"]

    def value_change_handler(self, stmt, fields):
        """Handle value changes."""
        var = (
            self._match_map[self._var_map[fields["var"]].name]
            if fields["var"] in self._var_map
            else None
        )
        if var is not None:
            value = fields["value"]
            var_name = self._var_map[fields["var"]]
            # try to match
            if not self._oneshot or (self._oneshot and not var.finished):
                var.new_state(value)
                if var.finished and not self._oneshot:
                    var.restart()

    def _match_callback(self, matcher_obj):
        """Match callback."""
