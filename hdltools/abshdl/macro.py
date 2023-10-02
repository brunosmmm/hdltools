"""HDL Macro declarations."""

from hdltools.abshdl import HDLObject


class HDLMacro(HDLObject):
    """Macro declaration."""

    def __init__(self, name, value):
        """Initialize."""
        self.name = name
        self.value = value

    def dumps(self):
        """Dump representation."""
        return "    CONST {}: {}".format(self.name, self.value)


class HDLMacroValue(HDLObject):
    """Usage of macros as placeholders."""

    def __init__(self, name):
        """Initialize."""
        self.name = name

    def dumps(self):
        """Dump representation."""
        return self.name
