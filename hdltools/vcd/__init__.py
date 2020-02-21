"""Value change dump stuff."""

from hdltools.sim import HDLSimulationPort


class VCDObject:
    """Abstract VCD object class."""

    def __init__(self, **kwargs):
        """Initialize."""
        pass


class VCDScope(VCDObject):
    """VCD scope."""

    def __init__(self, *scopes):
        """Initialize."""
        self._scopes = []
        for scope in scopes:
            if not isinstance(scope, str):
                raise TypeError("scope name must be string")
            if len(scope) < 1:
                # empty, ignore
                continue
            self._scopes.append(scope)

    def __repr__(self):
        """Get representation."""
        return "::".join(self._scopes)

    def __len__(self):
        """Get scope length."""
        return len(self._scopes)

    def __getitem__(self, idx):
        """Get scope by index."""
        return self._scopes[idx]

    def __eq__(self, other):
        """Scope equality."""
        if not isinstance(other, VCDScope):
            raise TypeError("other must be a VCDScope object")
        return self._scopes == other._scopes

    def contains(self, other):
        """Get whether this scope contains other scope."""
        if not isinstance(other, VCDScope):
            raise TypeError("other must be a VCDScope object")
        if len(self) >= len(other):
            # cannot contain, length must be less
            return False

        for idx, this_subscope in enumerate(self._scopes):
            if other[idx] != this_subscope:
                return False

        return True

    @staticmethod
    def from_str(scope_str):
        """Build from string."""
        if not isinstance(scope_str, str):
            raise TypeError("must be a string")
        scopes = scope_str.split("::")
        inclusive = len(scopes[-1]) < 1
        return (VCDScope(*scopes), inclusive)


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
    def scope(self):
        """Get scope."""
        return self._scope

    # FIXME: "identifiers" does not make sense, why would it be a list?
    @property
    def identifiers(self):
        """Get identifiers."""
        return self._identifiers

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


class VCDDump(VCDObject):
    """Complete VCD dump."""

    def __init__(self, name, timescale="1 ns", **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
        self.variables = {}
        self.variable_identifiers = {}
        self.timescale = timescale
        self.name = name
        self.initial = None
        self.vcd = []
        self.var_counter = ord("!")
        self.last_signal_values = None

    def _add_variable(self, var):
        self.variables[chr(self.var_counter)] = var
        self.variable_identifiers[var.get_first_identifier()] = chr(
            self.var_counter
        )
        self.var_counter += 1

    def add_variables(self, *args, **kwargs):
        """Add variables."""
        for arg in args:
            if not isinstance(arg, VCDVariable):
                raise TypeError("only VCDVariable allowed")
            self._add_variable(arg)

        for name, value in kwargs.items():
            if isinstance(value, HDLSimulationPort):
                var = VCDVariable(name, size=value.size)
            else:
                raise TypeError("not allowed")

            self._add_variable(var)

    @staticmethod
    def _combine_signals(sig_tuple):
        sig_dict = {}
        for d in sig_tuple:
            sig_dict.update(d)

        return sig_dict

    @staticmethod
    def _detect_changes(signals, psignals):
        int_signals = {name: int(value) for name, value in signals.items()}
        int_psignals = {name: int(value) for name, value in psignals.items()}
        changes = {}
        for name, value in int_signals.items():
            if value != int_psignals[name]:
                # change detected
                changes[name] = value

        return changes

    def load_dump(self, steps):
        """Load data."""
        for step in steps:
            sim_time, signals = step
            signals = self._combine_signals(signals)

            if sim_time == 0:
                self.initial = signals
                continue

            # look for changes
            if len(self.vcd) == 0:
                changes = self._detect_changes(signals, self.initial)
            else:
                changes = self._detect_changes(
                    signals, self.last_signal_values
                )

            formatted_changes = {}
            for name, value in changes.items():
                if self.variables[self.variable_identifiers[name]].size > 1:
                    formatted_changes[name] = "b{0:b} ".format(value)
                else:
                    formatted_changes[name] = "1" if bool(value) else "0"
            self.vcd.append(formatted_changes)
            self.last_signal_values = signals
