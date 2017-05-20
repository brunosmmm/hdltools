"""Common HDL declaration elements."""


class HDLObject:
    """Abstract class from which all HDL objects derive from."""

    pass


class HDLValue(HDLObject):
    """Abstract class for deriving other values."""

    def dumps(self):
        """Get representation."""
        pass

    def evaluate(self, **kwargs):
        """Evaluate and return value."""
        pass
