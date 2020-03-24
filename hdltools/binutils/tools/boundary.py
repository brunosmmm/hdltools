"""Function boundary."""

from hdltools.binutils.passes import AsmDumpPass
from hdltools.binutils import parse_objdump
from hdltools.binutils.function import AsmFunction


def get_boundaries(fn):
    """Get function boundaries."""
    if not isinstance(fn, AsmFunction):
        raise TypeError("fn must be AsmFunction object")
    start = fn.address
    candidates = []
    for instruction in fn.instructions:
        # HACK: no time to implement properly
        if "ret" in instruction.assembly:
            candidates.append(instruction.address)

    return (start, max(candidates))


def fn_boundary(asmdump, fn_name):
    """Get function boundaries."""

    dump_pass = AsmDumpPass()
    dump_pass.visit(parse_objdump(asmdump))

    for name, fn in dump_pass.get_functions().items():
        if name == fn_name:
            return get_boundaries(fn)

    return None
