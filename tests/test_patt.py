"""Test pattern matching."""

from hdltools.patterns import Pattern
from hdltools.patterns.matcher import PatternMatcher
from hdltools.vcd.parser import BaseVCDParser, VAR_PARSER
from hdltools.vcd.variable import VCDVariable


class VCDPatternMatcher(BaseVCDParser):
    """VCD pattern matcher."""

    def __init__(self):
        """Initialize."""
        super().__init__()
        self._match_map = {
            "data": PatternMatcher(
                Pattern("10000001"),
                Pattern("0"),
                match_cb=self._match_callback,
            )
        }
        self._var_map = {}

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
            print(f"DEBUG: {var_name} changed to {value}")
            # try to match
            is_match = var.new_state(value)
            if is_match:
                print("DEBUG: new state matches")

    def _match_callback(self, matcher_obj):
        """Match callback."""
        print("DEBUG: Sequence matched!")


def test_matcher():
    """Test sequential pattern matching."""
    with open("tests/assets/example.vcd", "r") as vcdfile:
        vcd_data = vcdfile.read()

    vparser = VCDPatternMatcher()
    vparser.parse(vcd_data)


if __name__ == "__main__":
    test_matcher()
