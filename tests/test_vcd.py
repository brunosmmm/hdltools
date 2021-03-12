"""Test VCD extensions."""

import pytest
from hdltools.vcd.parser import BaseVCDParser
from hdltools.vcd import VCDScope
from hdltools.vcd.history import VCDValueHistory, VCDValueHistoryEntry


def test_parser():
    """Test VCD parser."""
    with open("tests/assets/example.vcd", "r") as vcdfile:
        vcd_data = vcdfile.read()

    vparser = BaseVCDParser()
    vparser.parse(vcd_data)


def test_vcd_scope():
    """Test VCDScope."""
    scope = VCDScope("some", "scopes", "inside")
    similar_scope = VCDScope("some", "scopes", "inside")
    other_scope = VCDScope("some", "other", "scopes")
    contained_scope = VCDScope("some", "scopes", "inside", "scopes")

    assert scope != other_scope
    assert scope == similar_scope
    assert repr(scope) == "some::scopes::inside"
    assert scope.contains(contained_scope)
    assert not scope.contains(other_scope)
    assert len(scope) == 3
    assert scope[0] == "some"


def test_vcd_scope_fromstr():
    """Test building VCDScope from string."""

    scope, inclusive = VCDScope.from_str("VCD::Scope::example")
    assert inclusive is False
    scope, inclusive = VCDScope.from_str("VCD::Scope::example::")
    assert inclusive is True

    with pytest.raises(TypeError):
        VCDScope.from_str(123)


def test_vcd_value_history():
    """Test VCD value history."""
    scope_1, _ = VCDScope.from_str("outer::inner")
    scope_2, _ = VCDScope.from_str("outer::inner::deeper")
    scope_3, _ = VCDScope.from_str("outer::inner::deeper2")

    hist = VCDValueHistory()
    hist.add_entry(VCDValueHistoryEntry(scope_1, "foo", 0))
    hist.add_entry(VCDValueHistoryEntry(scope_2, "bar", 1))
    hist.add_entry(VCDValueHistoryEntry(scope_2, "bar_2", 2))
    hist.add_entry(VCDValueHistoryEntry(scope_3, "baz", 3))

    visited = hist.visited_scopes
    return visited


if __name__ == "__main__":
    test_parser()
    print(test_vcd_value_history())
