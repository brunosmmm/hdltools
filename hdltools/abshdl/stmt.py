"""General statements."""

from . import HDLObject


class HDLStatement(HDLObject):
    """Program statement."""

    _stmt_types = ['seq', 'par']

    def __init__(self, stmt_type):
        """Initialize."""
        if stmt_type not in self._stmt_types:
            raise KeyError('invalid statement type')

        self.stmt_type = stmt_type
