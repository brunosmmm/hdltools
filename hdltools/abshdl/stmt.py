"""General statements."""

from . import HDLObject


class HDLStatement(HDLObject):
    """Program statement."""

    _stmt_types = ['seq', 'par']

    def __init__(self, stmt_type, tag=None):
        """Initialize."""
        if stmt_type not in self._stmt_types:
            raise KeyError('invalid statement type')

        self.stmt_type = stmt_type
        self.tag = tag

    def set_tag(self, tag):
        """Set a tag."""
        self.tag = tag

    def get_tag(self):
        """Get tag."""
        return self.tag

    def is_legal(self):
        """Validate statement."""
        # Must be implemented in subclasses or will fail
        return False
