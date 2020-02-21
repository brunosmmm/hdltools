"""Test VCD extensions."""

import pytest
from hdltools.vcd.parser import BaseVCDParser
from hdltools.vcd import VCDScope


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

    assert (scope != other_scope)
    assert (scope == similar_scope)
    assert(repr(scope) == "some::scopes::inside")
    assert(scope.contains(contained_scope))
    assert(not scope.contains(other_scope))
    assert(len(scope) == 3)
    assert(scope[0] == "some")


    with pytest.raises(TypeError):
        scope == None

def test_vcd_scope_fromstr():
    """Test building VCDScope from string."""

    scope, inclusive = VCDScope.from_str("VCD::Scope::example")
    assert(inclusive is False)
    scope, inclusive = VCDScope.from_str("VCD::Scope::example::")
    assert(inclusive is True)

    with pytest.raises(TypeError):
        scope = VCDScope.from_str(123)



if __name__ == "__main__":
    test_parser()
