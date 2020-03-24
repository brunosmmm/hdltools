"""Instruction decoder."""


class InstructionDecoder:
    """Instruction decoder abstract class."""

    def decode(self, opcode):
        """Decode."""
        raise NotImplementedError

    def instruction_type(self, opcode):
        """Get instruction type."""
        raise NotImplementedError

    def insruction_class(self, opcode):
        """Get instruction class."""
        raise NotImplementedError
