"""HDLConcatenation insert with unevaluable sizes (HDLTOOLS-0001 B4)."""

from hdltools.abshdl.concat import HDLConcatenation
from hdltools.abshdl.const import HDLIntegerConstant
from hdltools.abshdl.expr import HDLExpression


def test_concat_insert_unevaluable_item_with_manual_size():
    """B4: insert parametric item with size= must be measurable afterward.

    Soft presence checks previously accepted inserts that left item.size=None,
    so len(concat) / pack() still raised ValueError.
    """
    placeholders = [HDLIntegerConstant(0, size=1, radix="b") for _ in range(8)]
    concat = HDLConcatenation(
        placeholders[0], *placeholders[1:], size=8, direction="rl"
    )
    expr = HDLExpression("FIELD_WIDTH")

    concat.insert(expr, offset=0, size=1)

    assert isinstance(concat.items[0], HDLExpression)
    assert "FIELD_WIDTH" in concat.items[0].dumps()
    assert concat.items[0].size == 1
    assert len(concat) == 8
