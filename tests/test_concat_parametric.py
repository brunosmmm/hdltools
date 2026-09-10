"""HDLConcatenation insert with unevaluable sizes (HDLTOOLS-0001 B4)."""

from hdltools.abshdl.concat import HDLConcatenation
from hdltools.abshdl.const import HDLIntegerConstant
from hdltools.abshdl.expr import HDLExpression


def test_concat_insert_unevaluable_item_with_manual_size():
    """B4: insert parametric/unevaluable item when size= is provided."""
    placeholders = [HDLIntegerConstant(0, size=1, radix="b") for _ in range(8)]
    concat = HDLConcatenation(
        placeholders[0], *placeholders[1:], size=8, direction="rl"
    )
    expr = HDLExpression("FIELD_WIDTH")  # len() unknown without size=

    concat.insert(expr, offset=0, size=1)

    assert any(
        isinstance(item, HDLExpression) and "FIELD_WIDTH" in item.dumps()
        for item in concat.items
    )
