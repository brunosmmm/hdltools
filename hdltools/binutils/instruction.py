"""Assembly instruction."""

from typing import Optional, Any
from enum import Enum, auto
from hdltools.binutils import AsmObject


class InstructionType(Enum):
    """Abstract instruction type."""

    UNKNOWN = auto()


class MemoryInstructionType(Enum):
    """Abstract memory instruction types."""

    LOAD = auto()
    STORE = auto()


class JumpInstructionType(Enum):
    """Abstract jump instruction types."""

    RELATIVE = auto()
    ABSOLUTE = auto()
    SUBROUTINE = auto()
    RETURN = auto()


class InstructionClass(Enum):
    """Abstract instruction classes."""

    MEMORY = auto()
    CONTROL = auto()
    ARITHMETIC = auto()
    LOGIC = auto()
    JUMP = auto()
    REGISTER = auto()
    UNKNOWN = auto()

    INSTRUCTION_TYPES = {
        MEMORY: MemoryInstructionType,
        JUMP: JumpInstructionType,
        UNKNOWN: InstructionType,
    }


class MetaAsmInstruction(type):
    """Metaclass for assembly instructions."""

    @property
    def instruction_class(cls):
        """Get instruction class."""
        return cls._CLASS

    @property
    def instruction_type(cls):
        """Get instruction type."""
        return cls._TYPE


class AsmInstruction(AsmObject, metaclass=MetaAsmInstruction):
    """Asm instruction."""

    _CLASS = InstructionClass.UNKNOWN
    _TYPE = InstructionType.UNKNOWN

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

    @property
    def instruction_class(self):
        """Get instruction class."""
        return type(self)._CLASS

    @property
    def instruction_type(self):
        """Get instruction type."""
        return type(self)._TYPE

    def __repr__(self):
        """Get representation."""
        return "{}: {} ({})".format(
            hex(self.address), hex(self.opcode), self.assembly
        )
