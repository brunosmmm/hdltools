"""General statements."""

from hdltools.abshdl import HDLObject


class HDLStatement(HDLObject):
    """Program statement."""

    _stmt_types = ["seq", "par", "null"]

    def __init__(self, stmt_type, tag=None, has_scope=False, **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
        if stmt_type not in self._stmt_types:
            raise KeyError("invalid statement type")

        self.stmt_type = stmt_type
        self.tag = tag
        self.has_scope = has_scope

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

    def get_scope(self):
        """Get scope if available."""
        return None

    def find_by_tag(self, tag):
        """Search in scope if available."""
        if self.has_scope is False:
            raise TypeError(
                "class {} has no scope".format(self.__class__.__name__)
            )

        scope = self.get_scope()
        if isinstance(scope, (tuple, list)):
            for _scope in scope:
                # returns just the first
                element = _scope.find_by_tag(tag)
                if element is not None:
                    return element
            return None
        else:
            return scope.find_by_tag(tag)

        return None
