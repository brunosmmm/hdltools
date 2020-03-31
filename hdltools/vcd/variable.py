"""VCD Variable."""

from hdltools.vcd import VCDObject, VCDScope


class VCDVariable(VCDObject):

    """Variable declaration."""

    def __init__(
        self, *identifiers, var_type="wire", size=1, name=None, scope=None
    ):
        """Initialize."""
        super().__init__()
        self._vartype = var_type
        self._size = size
        self._identifiers = identifiers
        self._name = name
        self._scope = scope
        self._aliases = []
        self._value = None
        self._last_changed = 0

    @property
    def var_type(self):
        """Get variable type."""
        return self._vartype

    @property
    def size(self):
        """Get variable size."""
        return self._size

    def __len__(self):
        """Get variable size."""
        return self.size

    @property
    def varid(self):
        """Get variable identifier."""
        return self._identifiers

    @property
    def name(self):
        """Get variable name."""
        return self._name

    @property
    def aliases(self):
        """Get aliases."""
        return self._aliases

    @property
    def scope(self):
        """Get scope."""
        return self._scope

    # FIXME: "identifiers" does not make sense, why would it be a list?
    @property
    def identifiers(self):
        """Get identifiers."""
        return self._identifiers

    @property
    def value(self):
        """Get last known value."""
        return self._value

    @value.setter
    def value(self, value):
        """Set value."""
        self._value = value

    @property
    def last_changed(self):
        """Get cycle when last changed."""
        return self._last_changed

    @last_changed.setter
    def last_changed(self, time):
        """Record change."""
        self._last_changed = time

    def add_alias(self, scope, name):
        """Add an alias."""
        self._aliases.append((scope, name))

    def get_first_identifier(self):
        """Get identifier."""
        if isinstance(self._identifiers, (tuple, list)):
            return self._identifiers[0]
        else:
            return self._identifiers

    @staticmethod
    def from_tokens(vtype, width, id, name, **kwargs):
        """Build from parser tokens."""
        scope = kwargs.get("scope", None)
        return VCDVariable(
            id, var_type=vtype, size=width, name=name, scope=scope
        )

    def __repr__(self):
        """Get representation."""
        scope_str = str(self._scope) + "::" if self._scope else ""
        return "{}{} ({})".format(scope_str, self._name, self._identifiers[0])

    def dump_aliases(self):
        """Get representation for aliases."""
        ret = []
        for scope, name in self._aliases:
            scope_str = str(scope) + "::" if scope else ""
            ret.append(
                "{}{} ({})".format(scope_str, name, self._identifiers[0])
            )

        return "\n".join(ret)

    def pack(self):
        """Pack into binary representation."""
        dump = {
            "vartype": self._vartype,
            "size": self._size,
            "identifiers": self._identifiers,
            "name": self._name,
            "scope": self._scope.pack(),
            "aliases": self._aliases,
        }
        return dump

    @staticmethod
    def unpack(src):
        """Unpack."""
        identifiers = src["identifiers"]
        scope, _ = VCDScope.from_str(src["scope"])
        var = VCDVariable(
            *identifiers,
            var_type=src["vartype"],
            size=src["size"],
            name=src["name"],
            scope=scope
        )
        for alias in src["aliases"]:
            var.add_alias(*alias)
        return var
