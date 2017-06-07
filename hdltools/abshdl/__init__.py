"""Common HDL declaration elements."""


class HDLObject:
    """Abstract class from which all HDL objects derive from."""

    def __init__(self, parent=None):
        """Initialize."""
        self.parent = parent

    def get_parent(self):
        """Get parent object."""
        return self.parent

    def set_parent(self, parent):
        """Set parent object."""
        self.parent = parent


class HDLValue(HDLObject):
    """Abstract class for deriving other values."""

    def dumps(self):
        """Get representation."""
        pass

    def evaluate(self, **kwargs):
        """Evaluate and return value."""
        pass
