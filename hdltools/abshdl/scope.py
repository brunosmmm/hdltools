"""Scope."""

from . import HDLObject
from .stmt import HDLStatement
from .comment import make_comment


class HDLScope(HDLObject):
    """Scope."""

    _scope_types = ['seq', 'par']

    def __init__(self, scope_type):
        """Initialize."""
        self.statements = []
        if scope_type not in self._scope_types:
            raise KeyError('invalid scope type')

        self.scope_type = scope_type

    def add(self, elements):
        """Add elements to scope."""
        for element in elements:
            if isinstance(element, str):
                self.statements.append(make_comment(element))
                continue
            if not isinstance(element, HDLStatement):
                print (element)
                raise TypeError('only HDLStatement allowed, got: '
                                '{}'.format(element.__class__.__name__))

            # check legality
            if element.stmt_type != self.scope_type\
               and element.stmt_type != 'null':
                raise ValueError('cannot add sequential statements '
                                 'in parallel scopes and vice versa')

            self.statements.append(element)

    def __len__(self):
        """Get statement count."""
        return len(self.statements)

    def __getitem__(self, _slice):
        """Get scope item."""
        return self.statements[_slice]

    def dumps(self):
        """Get intermediate representation."""
        return '\n'.join([x.dumps()+';' for x in self.statements])
