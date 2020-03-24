"""Assembly instruction."""

from typing import Optional, Any
from hdltools.binutils import AsmObject


class AsmInstruction(AsmObject):
    """Asm instruction."""

    def __init__(
        self,
        address: int,
        opcode: int,
        asm: Optional[str] = None,
        parent: Optional[Any] = None,
        **kwargs
    ):
        """Initialize."""
        super().__init__(**kwargs)
        self._addr = address
        self._opcode = opcode
        self._asm = asm
        self._parent = parent

    @property
    def address(self):
        """Get Address."""
        return self._addr

    @property
    def opcode(self):
        """Get opcode."""
        return self._opcode

    @property
    def assembly(self):
        """Get assembly text."""
        return self._asm

    @property
    def parent(self):
        """Get parent."""
        return self._parent

    def __repr__(self):
        """Get representation."""
        return "{}: {} ({})".format(
            hex(self.address), hex(self.opcode), self.assembly
        )
