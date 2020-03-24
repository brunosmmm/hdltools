"""Assembly function."""

from typing import Optional, Tuple
from hdltools.binutils.instruction import AsmInstruction
from hdltools.binutils import AsmObject


class AsmFunction(AsmObject):
    """Asm function."""

    def __init__(
        self,
        name: str,
        address: int,
        instructions: Optional[Tuple[AsmInstruction]] = None,
        **kwargs
    ):
        """Initialize."""
        super().__init__(**kwargs)
        self._name = name
        self._addr = address
        if instructions is not None:
            self._instructions = instructions
        else:
            self._instructions = []

    @property
    def name(self):
        """Get name."""
        return self._name

    @property
    def address(self):
        """Get address."""
        return self._addr

    @property
    def instructions(self):
        """Get instructions."""
        return self._instructions

    def __repr__(self):
        """Get representation."""
        return "{} @{}".format(self.name, hex(self.address))
