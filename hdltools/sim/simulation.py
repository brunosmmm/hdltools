"""Simulation object."""

from ..abshdl import HDLObject
from . import HDLSimulationObject


class HDLSimulation(HDLObject):
    """Simulation."""

    def __init__(self):
        """Initialize."""
        self.sim_objects = {}
        self.connection_matrix = {}
        self.current_time = 0
        self._signals = {}

    def add_stimulus(self, *stim):
        """Add stimulus."""
        for obj in stim:
            if not isinstance(obj, HDLSimulationObject):
                raise TypeError("only HDLSimulationObject allowed")

            if obj.identifier is None:
                identifier = obj.__class__.__name__
            else:
                identifier = obj.identifier

            self.sim_objects[identifier] = obj

            # add signals
            for name, out in obj.outputs.items():
                if obj.identifier is None:
                    identifier = obj.__class__.__name__
                else:
                    identifier = obj.identifier

                self._signals["{}.{}".format(identifier, name)] = out
            for name, inp in obj.inputs.items():
                if obj.identifier is None:
                    identifier = obj.__class__.__name__
                else:
                    identifier = obj.identifier

                self._signals["{}.{}".format(identifier, name)] = inp

    def simulate(self, stop_time):
        """Generate stimulus."""
        value_dump = []
        iterator = zip(
            *[
                obj.next({}, prefix=name)
                for name, obj in self.sim_objects.items()
            ]
        )
        for time, values in enumerate(iterator):
            self.current_time += 1
            # propagate
            self._propagate()
            if time == stop_time:
                break
            value_dump.append([time, values])

        return value_dump

    def _propagate(self):
        """Propagate values."""
        for name, signal in self._signals.items():
            if name not in self.connection_matrix:
                continue

            if signal.value_changed() is True:
                connections = self.connection_matrix[name]
                for connection in connections:
                    # update
                    self._signals[connection]._value_change(signal._value)

    def connect(self, outgoing, incoming):
        """Connect ports."""
        signals = self.signals
        if outgoing not in signals:
            raise IOError('port not found: "{}"'.format(outgoing))
        if incoming not in signals:
            raise IOError('port not found: "{}"'.format(incoming))

        if outgoing in self.connection_matrix:
            self.connection_matrix[outgoing] += [incoming]
        else:
            self.connection_matrix[outgoing] = set([incoming])

    @property
    def signals(self):
        """Get all identified signals."""
        return self._signals
