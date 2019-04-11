"""Value change dump stuff."""

from ..sim import HDLSimulationPort


class VCDObject:
    """Abstract class."""

    def __init__(self, **kwargs):
        """Initialize."""
        pass


class VCDVariable(VCDObject):
    """Variable declaration."""

    def __init__(self, *identifiers, var_type="wire", size=1):
        """Initialize."""
        super().__init__()
        self.var_type = var_type
        self.size = size
        self.identifiers = identifiers

    def get_first_identifier(self):
        """Get identifier."""
        if isinstance(self.identifiers, (tuple, list)):
            return self.identifiers[0]
        else:
            return self.identifiers


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
                changes = self._detect_changes(signals, self.last_signal_values)

            formatted_changes = {}
            for name, value in changes.items():
                if self.variables[self.variable_identifiers[name]].size > 1:
                    formatted_changes[name] = "b{0:b} ".format(value)
                else:
                    formatted_changes[name] = "1" if bool(value) else "0"
            self.vcd.append(formatted_changes)
            self.last_signal_values = signals
