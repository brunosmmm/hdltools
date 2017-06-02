"""Simulation objects."""

from ..abshdl import HDLObject
from ..abshdl.const import HDLIntegerConstant
from ..abshdl.expr import HDLExpression


class HDLSimulationPort(HDLObject):
    """Port representation."""

    def __init__(self, name, size=1, initial=0):
        """Initialize."""
        self.name = name
        self.size = size
        self.initial = initial
        self._value = initial
        self._edge = None
        self._changed = False

    def _value_change(self, value):
        """Record value change."""
        # for size of 1 bit only, detect edges
        if self.size == 1:
            if bool(self._value ^ value) is True:
                if bool(self._value) is True:
                    self._edge = 'fall'
                else:
                    self._edge = 'rise'
            else:
                self._edge = None
        else:
            self._changed = bool(self._value != value)

        self._value = value

    def rising_edge(self):
        """Is rising edge."""
        if self.size != 1:
            raise IOError('only applicable to ports of size 1')
        return bool(self._edge == 'rise')

    def falling_edge(self):
        """Is falling edge."""
        if self.size != 1:
            raise IOError('only applicable to ports of size 1')
        return bool(self._edge == 'fall')

    def value_changed(self):
        """Get value changed or not."""
        if self._edge is not None:
            return True

        return self._changed


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

    def next(self, input_states, **kwargs):
        """Get next value."""
        for x in iter(int, 1):
            self._sim_time += 1
            self.logic(input_states, **kwargs)
            yield self.get_outputs(**kwargs)

    def logic(self, input_states, **kwargs):
        """Do internal logic."""
        pass

    def output(self, name, size=1, initial=None):
        """Register output."""
        if name in self._outputs:
            raise ValueError('output already registered: {}'.format(name))
        self._outputs[name] = HDLSimulationPort(name, size)
        initial_value = 0
        if initial is not None:
            initial_value = initial
        return HDLIntegerConstant(initial_value, size=size)

    def input(self, name, size=1):
        """Register input."""
        if name in self._inputs:
            raise ValueError('input already registered: {}'.format(name))
        self._inputs[name] = HDLSimulationPort(name, size)
        return HDLIntegerConstant(0, size=size)

    def get_outputs(self, **kwargs):
        """Get output states."""
        outputs = {name: int(getattr(self, name)) for name in self._outputs}

        if 'prefix' in kwargs:
            prefix = kwargs.pop('prefix')
            return {'{}.{}'.format(prefix, name): value
                    for name, value in outputs.items()}

        return outputs

    def report_outputs(self, **kwargs):
        """Report registered outputs."""
        return self._outputs
