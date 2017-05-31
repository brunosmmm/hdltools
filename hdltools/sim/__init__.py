"""Simulation objects."""

from ..abshdl import HDLObject
from ..abshdl.const import HDLIntegerConstant
from ..abshdl.expr import HDLExpression


class HDLSimulationLogic:
    """Simulation logic wrapper."""

    def __init__(self, output_fn):
        """Initialize."""
        self.output_fn = output_fn

    def __call__(self, fn):
        """Decorate."""
        def wrapper_HDLSimulationLogic(*args, **kwargs):
            # infinite iterator
            for x in iter(int, 1):
                # process internal logic
                fn(*args, **kwargs)
                # generate current output statuses
                yield self.output_fn(*args, **kwargs)
        return wrapper_HDLSimulationLogic


class HDLSimulationObject(HDLObject):
    """Abstract class for simulation objects."""

    _outputs = []
    _inputs = []

    def __init__(self, identifier=None):
        """Initialize."""
        self.identifier = identifier
        self._sim_time = HDLIntegerConstant(0)

    @staticmethod
    def _get_constant(value, size=None):
        """Evaluate to constant value, if possible."""
        if isinstance(value, HDLExpression):
            try:
                return value.evaluate()
            except:
                raise ValueError('can only accept constant expressions.')
        elif isinstance(value, HDLIntegerConstant):
            return value
        elif isinstance(value, int):
            return HDLIntegerConstant(value, size)
        else:
            raise TypeError('type "{}" not supported'
                            .format(value.__class__.__name__))

    def next(self):
        """Get next value."""
        for x in iter(int, 1):
            self._sim_time += 1
            yield HDLIntegerConstant(0)

    def output(self, name, size=1):
        """Register output."""
        if name in self._outputs:
            raise ValueError('output already registered: {}'.format(name))
        self._outputs.append(name)
        return HDLIntegerConstant(0, size=size)

    def input(self, name, size=1):
        """Register input."""
        if name in self._inputs:
            raise ValueError('input already registered: {}'.format(name))
        self._inputs.append(name)
        return HDLIntegerConstant(0, size=size)

    def get_outputs(self, **kwargs):
        """Get output states."""
        outputs = {name: getattr(self, name) for name in self._outputs}

        if 'prefix' in kwargs:
            prefix = kwargs.pop('prefix')
            return {'{}.{}'.format(prefix, name): value
                    for name, value in outputs.items()}

        return outputs

    def report_outputs(self, **kwargs):
        """Report registered outputs."""
        return self._outputs


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
        iterator = zip(*[obj.next(prefix=name) for name, obj in
                         self.sim_objects.items()])
        for time, values in enumerate(iterator):
            self.current_time += 1
            if time == stop_time:
                break
            value_dump.append([time, values])

        return value_dump

    def report_signals(self):
        """Get all identified signals."""
        reported_signals = []
        for name, obj in self.sim_objects.items():
            for out in obj.report_outputs():
                if obj.identifier is None:
                    identifier = obj.__class__.__name__
                else:
                    identifier = obj.identifier

                reported_signals.append('{}.{}'.format(identifier,
                                                       out))

        return reported_signals
