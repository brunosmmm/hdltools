"""Scope."""

from . import HDLObject
from .stmt import HDLStatement


class HDLScope(HDLObject):
    """Scope."""

    _scope_types = ['seq', 'par']

    def __init__(self, scope_type):
        """Initialize."""
        self.statements = []
        if scope_type not in self._scope_types:
            raise KeyError('invalid scope type')

        self.scope_type = scope_type

    def add(self, element):
        """Add elements to scope."""
        if not isinstance(element, HDLStatement):
            raise TypeError('only HDLStatement allowed')

        self.statements.append(element)

    def __len__(self):
        """Get statement count."""
        return len(self.statements)

    def __getitem__(self, _slice):
        """Get scope item."""
        return self.statements[_slice]

    def dumps(self):
        """Get intermediate representation."""
        return '\n'.join([x.dumps() for x in self.statements])
