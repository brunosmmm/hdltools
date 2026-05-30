"""Simulation objects."""

from hdltools.abshdl import HDLObject
from hdltools.abshdl.const import HDLIntegerConstant
from hdltools.abshdl.expr import HDLExpression
from hdltools.logging import DEFAULT_LOGGER
from hdltools.sim.ports import HDLSimulationPort
from hdltools.sim.state import HDLSimulationState


class HDLSimulationObject(HDLObject):
    """Abstract class for simulation objects."""

    _sequential_methods = ["rising_edge", "falling_edge"]

    def __init__(self, identifier=None, **kwargs):
        """Initialize."""
        self._initialized = False
        self._structure_init = False
        self._outputs = {}
        self._inputs = {}
        self._attrs = {}
        self._variables = {}
        self.identifier = identifier
        self._sim_time = HDLIntegerConstant(0)

        # call parameter assignment
        self._parameters = self.parameters(**kwargs)

        # call structural generation method
        self.structure()
        self._structure_init = True

        # call state initialization
        self.initialstate()

        self._initialized = True
        super().__init__(**kwargs)

    def structure(self):
        """Structural generation."""

    def initialstate(self):
        """Initialize state."""

    def parameters(self, **kwargs):
        """Parameter initialization."""
        return kwargs

    def get_param(self, param_name):
        """Get parameter value."""
        return self._parameters[param_name]

    @staticmethod
    def _get_constant(value, size=None):
        """Evaluate to constant value, if possible."""
        if isinstance(value, HDLExpression):
            try:
                return value.evaluate()
            except (KeyError, TypeError, ValueError) as ex:
                raise ValueError("can only accept constant expressions.") from ex
        elif isinstance(value, HDLIntegerConstant):
            return value
        elif isinstance(value, int):
            return HDLIntegerConstant(value, size)
        else:
            raise TypeError(
                'type "{}" not supported'.format(value.__class__.__name__)
            )

    def input_changed(self, which_input, value):
        """Call on input changed."""

    def next(self, input_states, **kwargs):
        """Get next value."""
        for x in iter(int, 1):
            self._sim_time += 1
            self.set_inputs(input_states)
            self.logic(**kwargs)
            yield self.get_outputs(**kwargs)

    def logic(self, **kwargs):
        """Do internal logic."""

    def add_state(self, name, initial=None, attrs=None, **kwargs):
        """Add stateful logic element."""
        if self._initialized is True:
            raise RuntimeError("cannot add stateful logic after intialization")
        if name in self._variables:
            raise ValueError(
                "stateful element already registered: {}".format(name)
            )
        self._variables[name] = HDLSimulationState(
            name, initial=initial, **kwargs
        )
        if attrs is not None:
            self.set_attrs(name, attrs)

    def add_output(self, name, size=1, initial=0, attrs=None):
        """Register output."""
        if self._structure_init is True:
            raise RuntimeError("cannot add ports after initialization.")
        if name in self._outputs:
            raise ValueError("output already registered: {}".format(name))
        self._outputs[name] = HDLSimulationPort(name, size, initial=initial)
        if attrs is not None:
            self.set_attrs(name, attrs)

    def add_input(self, name, size=1, attrs=None):
        """Register input."""
        if self._structure_init is True:
            raise RuntimeError("cannot add ports after initialization.")
        if name in self._inputs:
            raise ValueError("input already registered: {}".format(name))
        self._inputs[name] = HDLSimulationPort(
            name, size, initial=0, change_cb=self.input_changed
        )
        if attrs is not None:
            self.set_attrs(name, attrs)

    def get_outputs(self, **kwargs):
        """Get output states."""
        outputs = {name: int(getattr(self, name)) for name in self._outputs}

        if "prefix" in kwargs:
            prefix = kwargs.pop("prefix")
            return {
                "{}.{}".format(prefix, name): value
                for name, value in outputs.items()
            }

        return outputs

    def set_inputs(self, input_values, **kwargs):
        """Set input states."""
        if "prefix" in kwargs:
            prefix = kwargs.pop("prefix")
        else:
            prefix = None

        for name, value in input_values.items():
            if prefix is not None:
                _prefix, _name = name.split(".")
                if _prefix != prefix:
                    # ignore
                    continue
            else:
                _name = name

            # set value
            setattr(self, _name, value)

    @property
    def outputs(self):
        """Report registered outputs."""
        return self._outputs

    @property
    def inputs(self):
        """Report registered inputs."""
        return self._inputs

    @property
    def state_elements(self):
        """Report registered stateful logic."""
        return self._variables

    def __setattr__(self, name, value):
        """Set an attribute."""
        if name.startswith("_") or self._initialized is False:
            super().__setattr__(name, value)
            return
        # check if it is a port
        if name in self._inputs:
            port = self._inputs[name]
        elif name in self._outputs:
            port = self._outputs[name]
        else:
            super().__setattr__(name, value)
            return
        if isinstance(port, HDLSimulationPort):
            # do magic stuff
            if value is None:
                raise ValueError("cannot set port to None")
            if isinstance(value, HDLSimulationPort):
                value = value.value
            elif isinstance(value, list):
                value = HDLSimulationPort.normalize_list_to_vector(value)
            changed = port._value_change(value)
            if changed:
                DEFAULT_LOGGER.debug(
                    f"value change: {self.identifier}.{name} -> {value}"
                )
            return

    def __getattr__(self, name):
        """Get an attribute."""
        if name in self._inputs:
            attr = self._inputs[name]
        elif name in self._outputs:
            attr = self._outputs[name]
        elif name in self._parameters:
            return self._parameters[name]
        else:
            raise AttributeError("invalid member: '{}'".format(name))
        if isinstance(attr, HDLSimulationPort):
            if len(attr) == 1:
                return bool(attr)
            return attr
        return attr

    def set_attrs(self, port, attrs):
        """Set special attributes."""
        self._attrs[port] = attrs

    def rising_edge(self, input_name):
        """Get if rising edge."""
        if input_name not in self._inputs:
            raise KeyError("invalid input: {}".format(input_name))

        return self._inputs[input_name].rising_edge()

    def falling_edge(self, input_name):
        """Get if falling edge."""
        if input_name not in self._inputs:
            raise KeyError("invalid input: {}".format(input_name))

        return self._inputs[input_name].falling_edge()
