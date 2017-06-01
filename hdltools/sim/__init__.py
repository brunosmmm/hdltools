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


class HDLSimulationPort(HDLObject):
    """Port representation."""

    def __init__(self, name, size=1):
        """Initialize."""
        self.name = name
        self.size = size


class HDLSimulationObject(HDLObject):
    """Abstract class for simulation objects."""

    def __init__(self, identifier=None):
        """Initialize."""
        self.identifier = identifier
        self._sim_time = HDLIntegerConstant(0)
        self._outputs = {}
        self._inputs = {}

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
        self._outputs[name] = HDLSimulationPort(name, size)
        return HDLIntegerConstant(0, size=size)

    def input(self, name, size=1):
        """Register input."""
        if name in self._inputs:
            raise ValueError('input already registered: {}'.format(name))
        self._inputs[name] = HDLSimulationPort(name, size)
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
