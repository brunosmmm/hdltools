"""Instances of other modules."""

from . import HDLObject
import hdltools.abshdl.module


class HDLInstance(HDLObject):
    """Instances."""

    def __init__(self, instance_name, instance_type):
        """Initialize."""
        if not isinstance(instance_type, hdltools.abshdl.module.HDLModule):
            raise TypeError(
                "argument instanc_type must be HDLModule or subclass type"
            )

        self._name = instance_name
        self._type = instance_type
        self._params = {}
        self._ports = {}

    @property
    def name(self):
        """Get name."""
        return self._name

    @property
    def itype(self):
        """Get type."""
        return self._type

    def attach_parameter_value(self, param_name, param_value):
        """Attach a value to a parameter."""
        inst_params = self._type.get_parameter_scope()
        if param_name not in inst_params:
            raise KeyError(
                "parameter '{}' not found in module '{}'".format(
                    param_name, self._type.name
                )
            )

        self._params[param_name] = param_value

    def connect_port(self, port_name, signal_name):
        """Connect instance port."""
        inst_ports = self._type.get_port_scope()
        if port_name not in inst_ports:
            raise KeyError(
                "port '{}' not found in module '{}'".format(
                    port_name, self._type.name
                )
            )
        self._ports[port_name] = signal_name

    @property
    def params(self):
        """Get params."""
        return self._params

    @property
    def ports(self):
        """Get ports."""
        return self._ports
