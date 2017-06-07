"""Scope."""

from . import HDLObject
from .stmt import HDLStatement
from .comment import make_comment
import types


class HDLScope(HDLObject):
    """Scope."""

    _scope_types = ['seq', 'par']

    def __init__(self, scope_type, **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
        self.statements = []
        if scope_type not in self._scope_types:
            raise KeyError('invalid scope type')

        self.scope_type = scope_type

    def _check_element(self, element):
        if isinstance(element, str):
            return make_comment(element)

        if not isinstance(element, HDLStatement):
            raise TypeError('only HDLStatement allowed, got: '
                            '{}'.format(element.__class__.__name__))

        # check legality
        if element.stmt_type != self.scope_type\
           and element.stmt_type != 'null':
            raise ValueError('cannot add sequential statements '
                             'in parallel scopes and vice versa,'
                             'tried {} into {} ({})'.format(element.stmt_type,
                                                            self.scope_type,
                                                            element.dumps()))

        return element

    def add(self, elements):
        """Add elements to scope."""
        if isinstance(elements, (tuple, list, types.GeneratorType)):
            for element in elements:
                self.statements.append(self._check_element(element))
                if isinstance(element, HDLObject):
                    element.set_parent(self)
        else:
            self.statements.append(self._check_element(elements))
            if isinstance(elements, HDLObject):
                elements.set_parent(self)

    def extend(self, scope):
        """Extend from another scope."""
        if not isinstance(scope, HDLScope):
            raise TypeError('only HDLScope allowed')

        if scope.scope_type != self.scope_type:
            raise ValueError('cannot extend from different type of scope')

        self.add(scope.statements)

    def insert(self, where, *elements):
        """Insert elements."""
        for index, element in enumerate(elements):
            self.statements.insert(where+index, self._check_element(element))
            if isinstance(element, HDLObject):
                element.set_parent(self)

    def insert_before(self, tag, *elements):
        """Insert before tag."""
        try:
            scope, element = self.find_by_tag(tag)
        except (ValueError, TypeError):
            raise IndexError('could not find tag:'
                             ' {}'.format(tag))

        self.insert(element[0], *elements)

    def insert_after(self, tag, *elements):
        """Insert after tag."""
        try:
            scope, element = self.find_by_tag(tag)
        except (ValueError, TypeError):
            raise IndexError('could not find tag:'
                             ' {}'.format(tag))

        scope.insert(element[0]+1, *elements)

    def get_tags(self):
        """Get available tags in this scope."""
        tags = []
        for statement in self.statements:
            if statement.tag is not None:
                tags.append(statement.tag)
        return tags

    def find_by_tag(self, tag):
        """Find element by tag."""
        for index, element in enumerate(self.statements):
            if element.tag == tag:
                return (self, (index, element))

            # recursion
            scopes = element.get_scope()
            if isinstance(scopes, HDLScope):
                # search
                _element = scopes.find_by_tag(tag)
                if _element is not None:
                    return _element
            elif isinstance(scopes, (list, tuple)):
                for scope in scopes:
                    _element = scope.find_by_tag(tag)
                    if _element is not None:
                        return _element

        return None

    def get_by_type(self, element_type):
        """Get list of elements by type."""
        element_list = []
        for element in self.statements:
            if isinstance(element, element_type):
                element_list.append(element)

        return element_list

    def __len__(self):
        """Get statement count."""
        return len(self.statements)

    def __getitem__(self, _slice):
        """Get scope item."""
        return self.statements[_slice]

    def dumps(self):
        """Get intermediate representation."""
        return '\n'.join([x.dumps() for x in self.statements])
