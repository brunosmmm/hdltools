"""Simulation object."""

from ..abshdl import HDLObject
from . import HDLSimulationObject


class HDLSimulation(HDLObject):
    """Simulation."""

    def __init__(self):
        """Initialize."""
        self.sim_objects = {}
        self.current_time = 0

    def add_stimulus(self, *stim):
        """Add stimulus."""
        for obj in stim:
            if not isinstance(obj, HDLSimulationObject):
                raise TypeError('only HDLSimulationObject allowed')

            if obj.identifier is None:
                identifier = obj.__class__.__name__
            else:
                identifier = obj.identifier

            self.sim_objects[identifier] = obj

    def simulate(self, stop_time):
        """Generate stimulus."""
        value_dump = []
        iterator = zip(*[obj.next(None, prefix=name) for name, obj in
                         self.sim_objects.items()])
        for time, values in enumerate(iterator):
            self.current_time += 1
            if time == stop_time:
                break
            value_dump.append([time, values])

        return value_dump

    def report_signals(self):
        """Get all identified signals."""
        reported_signals = {}
        for name, obj in self.sim_objects.items():
            for name, out in obj.report_outputs().items():
                if obj.identifier is None:
                    identifier = obj.__class__.__name__
                else:
                    identifier = obj.identifier

                reported_signals['{}.{}'.format(identifier,
                                                name)] = out

        return reported_signals
