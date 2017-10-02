"""HDL Macro declarations."""

from . import (HDLObject)


class HDLMacro(HDLObject):
    """Macro declaration."""

    def __init__(self, name, value):
        """Initialize."""
        self.name = name
        self.value = value

    def dumps(self):
        """Dump representation."""
        return '    CONST {}: {}'.format(self.name, self.value)
