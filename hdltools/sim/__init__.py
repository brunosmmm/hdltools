"""Simulation objects."""

from ..abshdl import HDLObject
from ..abshdl.const import HDLIntegerConstant
from ..abshdl.expr import HDLExpression


class HDLSimulationPort(HDLObject):
    """Port representation."""

    def __init__(self, name, size=1, initial=0, change_cb=None):
        """Initialize."""
        self.name = name
        self.size = size
        self.initial = initial
        self._value = initial
        self._edge = None
        self._changed = False
        self._change_cb = change_cb

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

        if self._value != value:
            if self._change_cb is not None:
                self._change_cb(self.name, self._value)

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
        return bool(self._edge is not None or self._changed is True)


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
            self.set_inputs(input_states)
            self.logic(**kwargs)
            yield self.get_outputs(**kwargs)

    def logic(self, **kwargs):
        """Do internal logic."""
        pass

    def output(self, name, size=1, initial=0):
        """Register output."""
        if name in self._outputs:
            raise ValueError('output already registered: {}'.format(name))
        self._outputs[name] = HDLSimulationPort(name, size, initial=initial)
        return self._outputs[name]

    def input(self, name, size=1):
        """Register input."""
        if name in self._inputs:
            raise ValueError('input already registered: {}'.format(name))
        self._inputs[name] = HDLSimulationPort(name, size, initial=0)
        return self._inputs[name]

    def get_outputs(self, **kwargs):
        """Get output states."""
        outputs = {name: int(getattr(self, name)) for name in self._outputs}

        if 'prefix' in kwargs:
            prefix = kwargs.pop('prefix')
            return {'{}.{}'.format(prefix, name): value
                    for name, value in outputs.items()}

        return outputs

    def set_inputs(self, input_values, **kwargs):
        """Set input states."""
        if 'prefix' in kwargs:
            prefix = kwargs.pop('prefix')
        else:
            prefix = None

        for name, value in input_values.items():
            if prefix is not None:
                _prefix, _name = name.split('.')
                if _prefix != prefix:
                    # ignore
                    continue
            else:
                _name = name

            # set value
            setattr(self, _name, value)

    def report_outputs(self, **kwargs):
        """Report registered outputs."""
        return self._outputs

    def __setattr__(self, name, value):
        """Set an attribute."""
        if not hasattr(self, name):
            super().__setattr__(name, value)
        else:
            port = getattr(self, name)
            if isinstance(port, HDLSimulationPort):
                # do magic stuff
                if value is None:
                    raise ValueError('cannot set port to None')
                port._value_change(value)
            else:
                # do normal stuff
                super().__setattr__(name, value)

    def __getattribute__(self, name):
        """Get an attribute."""
        attr = super().__getattribute__(name)
        if isinstance(attr, HDLSimulationPort):
            return attr._value
        else:
            return attr
